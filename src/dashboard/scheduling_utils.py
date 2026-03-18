from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from src.dashboard.config import API_BASE_URL_ENV, PENDING_FILE, SCHEDULED_FILE
from src.dashboard.data_utils import read_json_list, write_json_list
from src.dashboard.media_utils import parse_publish_time, to_utc_iso_z


def _slot_key(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def build_scheduled_key(row: dict[str, Any]) -> str:
    item_id = str(row.get("item_id", "")).strip()
    if item_id:
        return f"item:{item_id}"
    post_url = str(row.get("Post URL", "")).strip()
    if post_url:
        return f"url:{post_url}"
    title = str(row.get("title", "")).strip()
    publish_time = str(row.get("publish_time", "")).strip()
    return f"title:{title}|time:{publish_time}"


def toggle_scheduled_lock(schedule_key: str) -> tuple[bool, str]:
    if os.getenv(API_BASE_URL_ENV, "").strip():
        return False, "当前为 API 数据源模式，已禁用本地样本写入。"

    scheduled_rows = read_json_list(SCHEDULED_FILE)
    target_idx = next((idx for idx, row in enumerate(scheduled_rows) if build_scheduled_key(row) == schedule_key), -1)
    if target_idx < 0:
        return False, "未找到目标已排程贴文，可能已被更新。"

    row = scheduled_rows[target_idx]
    current_locked = bool(row.get("is_locked", False))
    row["is_locked"] = not current_locked
    row["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json_list(SCHEDULED_FILE, scheduled_rows)
    return True, "已锁定该排程窗口。" if row["is_locked"] else "已取消锁定。"


def move_scheduled_item_to_pending(schedule_key: str) -> tuple[bool, str]:
    if os.getenv(API_BASE_URL_ENV, "").strip():
        return False, "当前为 API 数据源模式，已禁用本地样本写入。"

    pending_rows = read_json_list(PENDING_FILE)
    scheduled_rows = read_json_list(SCHEDULED_FILE)
    target_idx = next((idx for idx, row in enumerate(scheduled_rows) if build_scheduled_key(row) == schedule_key), -1)
    if target_idx < 0:
        return False, "未找到目标已排程贴文，可能已被更新。"

    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat().replace("+00:00", "Z")
    row = scheduled_rows.pop(target_idx)
    if not str(row.get("item_id", "")).strip():
        row["item_id"] = f"unscheduled-{int(now_utc.timestamp())}"
    row["publish_time"] = now_iso
    row["updated_at"] = now_iso
    row["review_status"] = "waiting"
    row["is_locked"] = False
    pending_rows.append(row)

    write_json_list(SCHEDULED_FILE, scheduled_rows)
    write_json_list(PENDING_FILE, pending_rows)
    return True, "已取消排程并返回已出未排。"


def move_pending_item_to_scheduled(
    item_id: str,
    schedule_hkt: datetime,
    window_minutes: int,
    lock_after_schedule: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    if os.getenv(API_BASE_URL_ENV, "").strip():
        return False, "当前为 API 数据源模式，已禁用本地样本写入。", {}
    step = int(window_minutes) if int(window_minutes) > 0 else 10
    if 60 % step != 0:
        return False, "排程窗口必须能整除 60 分钟。", {}
    if schedule_hkt.minute % step != 0:
        return False, f"仅支持每 {step} 分钟窗口。", {}
    now_local = datetime.now(schedule_hkt.tzinfo or timezone.utc).replace(second=0, microsecond=0)
    if schedule_hkt.replace(second=0, microsecond=0) <= now_local:
        return False, "不能设置过去时间，请选择当前之后的时间窗口。", {}

    pending_rows = read_json_list(PENDING_FILE)
    scheduled_rows = read_json_list(SCHEDULED_FILE)
    target_idx = next((idx for idx, row in enumerate(pending_rows) if str(row.get("item_id", "")) == item_id), -1)
    if target_idx < 0:
        return False, "未找到目标待排程贴文，可能已被其他操作处理。", {}

    schedule_at = schedule_hkt.replace(second=0, microsecond=0)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    locked_slots: set[datetime] = set()
    locked_by_slot: dict[datetime, list[dict[str, Any]]] = {}
    unlocked_by_slot: dict[datetime, list[dict[str, Any]]] = {}
    for existing in scheduled_rows:
        publish_dt = parse_publish_time(str(existing.get("publish_time", "")))
        if publish_dt is None:
            continue
        slot_dt = _slot_key(publish_dt)
        if bool(existing.get("is_locked", False)):
            locked_slots.add(slot_dt)
            locked_by_slot.setdefault(slot_dt, []).append(existing)
            continue
        unlocked_by_slot.setdefault(slot_dt, []).append(existing)

    if schedule_at in locked_slots:
        return False, "目标时间窗口已被锁定，不能写入新排程。", {}

    # Localized squeeze chain:
    # only rows in the collided slot are pushed, then continue only if the next
    # slot was already occupied (or locked) by the pushed rows.
    shifted_rows: list[dict[str, str]] = []
    skipped_locked_rows: list[dict[str, str]] = []
    seen_locked_keys: set[str] = set()
    carry_rows = unlocked_by_slot.pop(schedule_at, [])
    next_slot = schedule_at + timedelta(minutes=step)
    while carry_rows:
        while next_slot in locked_slots:
            for locked_row in locked_by_slot.get(next_slot, []):
                row_key = build_scheduled_key(locked_row)
                if row_key in seen_locked_keys:
                    continue
                seen_locked_keys.add(row_key)
                skipped_locked_rows.append(
                    {
                        "title": str(locked_row.get("title", "N/A")),
                        "locked_time": next_slot.strftime("%Y-%m-%d %H:%M"),
                    }
                )
            next_slot = next_slot + timedelta(minutes=step)
        existing_rows = unlocked_by_slot.pop(next_slot, [])
        for row in carry_rows:
            old_slot = _slot_key(parse_publish_time(str(row.get("publish_time", ""))) or schedule_at)
            row["publish_time"] = to_utc_iso_z(next_slot)
            row["updated_at"] = now_iso
            shifted_rows.append(
                {
                    "title": str(row.get("title", "N/A")),
                    "old_time": old_slot.strftime("%Y-%m-%d %H:%M"),
                    "new_time": next_slot.strftime("%Y-%m-%d %H:%M"),
                }
            )
        carry_rows = existing_rows
        next_slot = next_slot + timedelta(minutes=step)

    row = pending_rows.pop(target_idx)
    row["publish_time"] = to_utc_iso_z(schedule_at)
    row["updated_at"] = now_iso
    row["review_status"] = "scheduled"
    row["is_locked"] = bool(lock_after_schedule)
    scheduled_rows.append(row)

    write_json_list(PENDING_FILE, pending_rows)
    write_json_list(SCHEDULED_FILE, scheduled_rows)
    report = {
        "shifted_rows": shifted_rows,
        "skipped_locked_rows": skipped_locked_rows,
    }
    return True, "已完成排程并更新本地样本数据。", report
