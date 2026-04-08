from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.dashboard.config import CATEGORY_ORDER, HKT_TZ, PENDING_FILE, PUBLISHED_FILE, SCHEDULED_FILE
from src.dashboard.data_utils import read_json_list, write_json_list
from src.dashboard.media_utils import parse_publish_time
from src.dashboard_api.cms_client import CmsActionClient


def _safe_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def _build_action_key(item: dict[str, Any]) -> str:
    post_link_id = str(item.get("post_link_id", "")).strip()
    if post_link_id:
        return f"plink:{post_link_id}"
    post_id = str(item.get("post_id", "")).strip()
    post_url = str(item.get("Post URL", "")).strip()
    publish_time = str(item.get("publish_time", "")).strip()
    title = str(item.get("title", "")).strip()
    return f"pid:{post_id}|url:{post_url}|time:{publish_time}|title:{title}"


def _extract_action_ids(item: dict[str, Any]) -> tuple[int, str]:
    post_id = _safe_int(item.get("post_id", 0))
    if post_id <= 0:
        post_id = _safe_int(item.get("item_id", 0))
    post_link_id = str(item.get("post_link_id", "")).strip()
    return post_id, post_link_id


def _to_hkt_input_time(dt_hkt: datetime) -> str:
    return dt_hkt.strftime("%Y-%m-%dT%H:%M")


def _validate_update_time_and_window(
    *,
    picked_dt: datetime,
    now_hkt: datetime,
    window_minutes: int,
    scheduled_items: list[tuple[datetime, dict[str, Any]]],
    target_action_key: str,
) -> tuple[bool, str]:
    step = int(window_minutes) if int(window_minutes) > 0 else 10
    if picked_dt.minute % step != 0:
        return False, f"time must align to {step} minutes"
    if picked_dt <= now_hkt.replace(second=0, microsecond=0):
        return False, "cannot set past time"
    picked_slot = picked_dt.replace(second=0, microsecond=0)
    for dt, row in scheduled_items:
        if _build_action_key(row) == target_action_key:
            continue
        if bool(row.get("is_locked", False)) and dt.replace(second=0, microsecond=0) == picked_slot:
            return False, "target slot is locked"
    return True, ""


def _collect_time_sorted_items(items: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    rows: list[tuple[datetime, dict[str, Any]]] = []
    for row in items:
        dt = parse_publish_time(str(row.get("publish_time", "")))
        if dt:
            rows.append((dt, row))
    return rows


def _pending_rows_with_sort_dt(rows: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    """已出未排：优先 publish_time，失败则用 updated_at，再失败则用 epoch（仅在该分类启用兜底全量时可见）。"""
    epoch_hkt = datetime(1970, 1, 1, tzinfo=timezone.utc).astimezone(HKT_TZ)
    out: list[tuple[datetime, dict[str, Any]]] = []
    for row in rows:
        dt = parse_publish_time(str(row.get("publish_time", "")))
        if not dt:
            dt = parse_publish_time(str(row.get("updated_at", "")))
        if not dt:
            dt = epoch_hkt
        out.append((dt, row))
    return out


def _plan_publish_slot_adjustments(
    schedule_dt: datetime,
    scheduled_items: list[tuple[datetime, dict[str, Any]]],
    window_minutes: int,
) -> tuple[bool, str, list[dict[str, Any]], dict[str, Any]]:
    step = window_minutes if window_minutes > 0 else 10
    target_slot = schedule_dt.replace(second=0, microsecond=0)
    if target_slot.minute % step != 0:
        return False, f"time must align to {step} minutes", [], {}

    locked_slots: set[datetime] = set()
    locked_rows: dict[datetime, list[dict[str, Any]]] = {}
    unlocked_rows: dict[datetime, list[dict[str, Any]]] = {}
    for dt, row in scheduled_items:
        slot = dt.replace(second=0, microsecond=0)
        if bool(row.get("is_locked", False)):
            locked_slots.add(slot)
            locked_rows.setdefault(slot, []).append(row)
        else:
            unlocked_rows.setdefault(slot, []).append(row)
    if target_slot in locked_slots:
        return False, "target slot is locked", [], {}

    carry_rows = unlocked_rows.pop(target_slot, [])
    next_slot = target_slot + timedelta(minutes=step)
    pre_updates: list[dict[str, Any]] = []
    shifted_rows: list[dict[str, str]] = []
    skipped_locked_rows: list[dict[str, str]] = []
    seen_locked: set[str] = set()

    while carry_rows:
        while next_slot in locked_slots:
            for row in locked_rows.get(next_slot, []):
                key = _build_action_key(row)
                if key in seen_locked:
                    continue
                seen_locked.add(key)
                skipped_locked_rows.append(
                    {"title": str(row.get("title", "N/A")), "locked_time": next_slot.strftime("%Y-%m-%d %H:%M")}
                )
            next_slot = next_slot + timedelta(minutes=step)

        existing_rows = unlocked_rows.pop(next_slot, [])
        for row in carry_rows:
            post_id, post_link_id = _extract_action_ids(row)
            if post_id <= 0 or not post_link_id:
                return False, "scheduled row missing post_id/post_link_id for shift", [], {}
            old_dt = parse_publish_time(str(row.get("publish_time", ""))) or target_slot
            pre_updates.append(
                {
                    "post_id": post_id,
                    "post_link_id": post_link_id,
                    "post_message": str(row.get("post_message", "")).strip(),
                    "post_link_type": str(row.get("post_link_type", "link")).strip() or "link",
                    "image_url": str(row.get("image_url", "")).strip(),
                    "post_mp4_url": str(row.get("post_mp4_url", "")).strip(),
                    "post_link_time": _to_hkt_input_time(next_slot),
                    "_old_ts": int(old_dt.timestamp()),
                }
            )
            shifted_rows.append(
                {
                    "title": str(row.get("title", "N/A")),
                    "old_time": old_dt.strftime("%Y-%m-%d %H:%M"),
                    "new_time": next_slot.strftime("%Y-%m-%d %H:%M"),
                }
            )
        carry_rows = existing_rows
        next_slot = next_slot + timedelta(minutes=step)

    pre_updates.sort(key=lambda x: int(x.get("_old_ts", 0)), reverse=True)
    for row in pre_updates:
        row.pop("_old_ts", None)
    return True, "", pre_updates, {"shifted_rows": shifted_rows, "skipped_locked_rows": skipped_locked_rows}


def _read_default_session_settings() -> dict[str, Any]:
    settings_file = Path(__file__).resolve().parents[2] / "data" / "samples" / "dashboard_settings_state.json"
    try:
        raw = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}
        sessions = raw.get("sessions", {}) if isinstance(raw.get("sessions", {}), dict) else {}
        default = sessions.get("default", {}) if isinstance(sessions.get("default", {}), dict) else {}
        return default if isinstance(default, dict) else {}
    except Exception:
        return {}


def _refresh_live_sample_files(default_session: dict[str, Any]) -> dict[str, Any]:
    """Pull fb_published / fb_scheduled / posts from CMS and rewrite sample JSON files."""
    from src.dashboard.live_api_sync import sync_live_data_to_sample_files

    enable_alias = bool(default_session.get("cfg_enable_category_alias_mode", False))
    target_fan = str(default_session.get("cfg_target_fan_page_id", "350584865140118")).strip() or "350584865140118"
    try:
        sync_live_data_to_sample_files.clear()
    except Exception:
        pass
    return sync_live_data_to_sample_files(
        enable_category_alias_mode=enable_alias,
        target_fan_page_id=target_fan,
    )


def _sync_live() -> dict[str, Any]:
    return _refresh_live_sample_files(_read_default_session_settings())


def load_board_columns(includes: list[str] | None = None) -> dict[str, Any]:
    default_session = _read_default_session_settings()
    sync_result = _refresh_live_sample_files(default_session)
    cms_upstream_calls: list[dict[str, Any]] = []
    if isinstance(sync_result, dict):
        raw_calls = sync_result.get("cms_upstream_calls")
        if isinstance(raw_calls, list):
            cms_upstream_calls = raw_calls

    now_hkt = datetime.now(HKT_TZ)
    past_24h = now_hkt - timedelta(hours=24)
    next_24h = now_hkt + timedelta(hours=24)

    published_items = _collect_time_sorted_items(read_json_list(PUBLISHED_FILE))
    scheduled_items = _collect_time_sorted_items(read_json_list(SCHEDULED_FILE))
    pending_pairs = _pending_rows_with_sort_dt(read_json_list(PENDING_FILE))

    published_windowed = [
        item
        for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)
        if past_24h <= dt <= now_hkt
    ]
    scheduled_windowed = [item for dt, item in sorted(scheduled_items, key=lambda x: x[0]) if now_hkt <= dt <= next_24h]

    pending_windowed_by_category: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORY_ORDER}
    for dt, row in sorted(pending_pairs, key=lambda x: x[0], reverse=True):
        if not (past_24h <= dt <= now_hkt):
            continue
        category = str(row.get("category", ""))
        if category in pending_windowed_by_category:
            pending_windowed_by_category[category].append(row)

    published_all = [item for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)]
    scheduled_all = [item for dt, item in sorted(scheduled_items, key=lambda x: x[0])]
    pending_all_by_category: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORY_ORDER}
    for dt, row in sorted(pending_pairs, key=lambda x: x[0], reverse=True):
        category = str(row.get("category", ""))
        if category in pending_all_by_category:
            pending_all_by_category[category].append(row)

    fallback_mode_enabled = bool(
        default_session.get("cfg_enable_board_fallback_mode", default_session.get("enable_board_fallback_mode", False))
    )

    # 与 Streamlit 侧一致：兜底按「列」独立判断。旧实现用「已發佈或任一分類有待排」绑死三列，
    # 会导致某一分类在 24h 内为空时永远不兜底，即使用户已勾选「看板渲染兜底」。
    use_fallback_published = bool(fallback_mode_enabled and not published_windowed)
    use_fallback_scheduled = bool(fallback_mode_enabled and not scheduled_windowed)
    published = published_all if use_fallback_published else published_windowed
    scheduled = scheduled_all if use_fallback_scheduled else scheduled_windowed

    pending_by_category: dict[str, list[dict[str, Any]]] = {}
    for cat in CATEGORY_ORDER:
        win_list = pending_windowed_by_category[cat]
        full_list = pending_all_by_category[cat]
        if fallback_mode_enabled and not win_list:
            pending_by_category[cat] = full_list
        else:
            pending_by_category[cat] = win_list

    payload = {
        "published": published,
        "scheduled": scheduled,
        "pending_by_category": pending_by_category,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cms_upstream_calls": cms_upstream_calls,
    }
    if not includes:
        return payload

    include_set = {x.strip() for x in includes if x.strip()}
    filtered_pending: dict[str, list[dict[str, Any]]] = {}
    if any(x.startswith("pending:") for x in include_set):
        for token in include_set:
            if token.startswith("pending:"):
                cat = token.split(":", 1)[1].strip()
                if cat:
                    filtered_pending[cat] = payload["pending_by_category"].get(cat, [])
    elif "pending" in include_set:
        filtered_pending = payload["pending_by_category"]

    return {
        "published": payload["published"] if "published" in include_set else [],
        "scheduled": payload["scheduled"] if "scheduled" in include_set else [],
        "pending_by_category": filtered_pending,
        "generated_at": payload["generated_at"],
        "cms_upstream_calls": payload["cms_upstream_calls"],
    }


def publish_from_pending(item_id: str, schedule_time: str, window_minutes: int = 10) -> dict[str, Any]:
    pending_rows = read_json_list(PENDING_FILE)
    scheduled_rows = read_json_list(SCHEDULED_FILE)
    target = next((x for x in pending_rows if str(x.get("item_id", "")).strip() == item_id.strip()), None)
    if not target:
        return {"ok": False, "message": "pending item not found"}

    try:
        schedule_dt = datetime.strptime(schedule_time.strip(), "%Y-%m-%dT%H:%M").replace(tzinfo=HKT_TZ)
    except ValueError:
        return {"ok": False, "message": "invalid schedule_time format, expected YYYY-MM-DDTHH:mm"}
    now_hkt = datetime.now(HKT_TZ).replace(second=0, microsecond=0)
    if schedule_dt <= now_hkt:
        return {"ok": False, "message": "cannot schedule in the past"}

    ok_plan, plan_message, pre_updates, impact = _plan_publish_slot_adjustments(
        schedule_dt=schedule_dt,
        scheduled_items=_collect_time_sorted_items(scheduled_rows),
        window_minutes=window_minutes,
    )
    if not ok_plan:
        return {"ok": False, "message": plan_message}

    client = CmsActionClient()
    for row in pre_updates:
        update_result = client.run_action(
            "fb_update",
            {
                "post_id": int(row.get("post_id", 0)),
                "post_link_id": str(row.get("post_link_id", "")),
                "post_message": str(row.get("post_message", "")),
                "post_link_time": str(row.get("post_link_time", "")),
                "post_link_type": str(row.get("post_link_type", "link")),
                "image_url": str(row.get("image_url", "")) or None,
                "post_mp4_url": str(row.get("post_mp4_url", "")) or None,
            },
        )
        if not bool(update_result.get("ok")):
            return {"ok": False, "message": f"shift update failed: {update_result.get('message', 'unknown')}"}

    publish_result = client.run_action(
        "fb_publish",
        {
            "post_id": int(target.get("post_id", 0)),
            "post_message": str(target.get("post_message", "")).strip() or str(target.get("title", "")).strip(),
            "post_link_time": schedule_time.strip(),
            "post_link_type": str(target.get("post_link_type", "link")).strip() or "link",
            "image_url": str(target.get("image_url", "")).strip() or None,
            "post_mp4_url": str(target.get("post_mp4_url", "")).strip() or None,
            "post_timezone": "Asia/Hong_Kong",
        },
    )
    if not bool(publish_result.get("ok")):
        return {"ok": False, "message": str(publish_result.get("message", "publish failed"))}

    sync_result = _sync_live()
    return {"ok": True, "message": "publish ok", "impact_report": impact, "sync_result": sync_result}


def update_scheduled(payload: dict[str, Any]) -> dict[str, Any]:
    enforce_window = bool(payload.get("enforce_time_validation", True))
    if enforce_window:
        picked_time = str(payload.get("post_link_time", "")).strip()
        try:
            picked_dt = datetime.strptime(picked_time, "%Y-%m-%dT%H:%M").replace(tzinfo=HKT_TZ)
        except ValueError:
            return {"ok": False, "message": "invalid time format, expected YYYY-MM-DDTHH:mm"}
        ok_time, msg_time = _validate_update_time_and_window(
            picked_dt=picked_dt,
            now_hkt=datetime.now(HKT_TZ),
            window_minutes=int(payload.get("window_minutes", 10) or 10),
            scheduled_items=_collect_time_sorted_items(read_json_list(SCHEDULED_FILE)),
            target_action_key=str(payload.get("target_action_key", "")).strip(),
        )
        if not ok_time:
            return {"ok": False, "message": msg_time}

    client = CmsActionClient()
    action_payload = {
        "post_id": int(payload.get("post_id", 0)),
        "post_link_id": str(payload.get("post_link_id", "")).strip(),
        "post_message": str(payload.get("post_message", "")).strip(),
        "post_link_time": str(payload.get("post_link_time", "")).strip(),
        "post_link_type": str(payload.get("post_link_type", "link")).strip() or "link",
        "image_url": str(payload.get("image_url", "")).strip() or None,
        "post_mp4_url": str(payload.get("post_mp4_url", "")).strip() or None,
    }
    result = client.run_action("fb_update", action_payload)
    if not bool(result.get("ok")):
        return {"ok": False, "message": str(result.get("message", "update failed"))}
    return {"ok": True, "message": "update ok", "sync_result": _sync_live()}


def delete_scheduled(post_id: int, post_link_id: str) -> dict[str, Any]:
    client = CmsActionClient()
    result = client.run_action("fb_delete", {"post_id": int(post_id), "post_link_id": str(post_link_id).strip()})
    if not bool(result.get("ok")):
        return {"ok": False, "message": str(result.get("message", "delete failed"))}
    return {"ok": True, "message": "delete ok", "sync_result": _sync_live()}


def toggle_lock(action_key: str) -> dict[str, Any]:
    scheduled_rows = read_json_list(SCHEDULED_FILE)
    idx = next((i for i, row in enumerate(scheduled_rows) if _build_action_key(row) == action_key), -1)
    if idx < 0:
        return {"ok": False, "message": "scheduled item not found"}
    row = scheduled_rows[idx]
    row["is_locked"] = not bool(row.get("is_locked", False))
    row["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json_list(SCHEDULED_FILE, scheduled_rows)
    return {"ok": True, "message": "lock toggled", "is_locked": bool(row["is_locked"])}

