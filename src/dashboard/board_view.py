from __future__ import annotations

import calendar
import json
import textwrap
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.dashboard.config import (
    CATEGORY_CLASS_MAP,
    CATEGORY_ORDER,
    DEFAULT_SCHEDULE_WINDOW_MINUTES,
    HKT_TZ,
    SCHEDULE_WINDOW_OPTIONS,
    WORKSPACE_ROOT,
)
from src.dashboard.data_utils import load_pending_base, load_published_items, load_scheduled_items
from src.dashboard.fb_action_client import FBActionClient
from src.dashboard.frontend_templates import build_chip_color_script, build_schedule_pick_script
from src.dashboard.live_api_sync import sync_live_data_to_sample_files
from src.dashboard.media_utils import parse_publish_time, resolve_thumbnail_src, round_up_to_window
from src.dashboard.scheduling_utils import (
    build_scheduled_key,
    toggle_scheduled_lock,
)
from src.dashboard.style_utils import category_style_tokens

UI_DEBUG_LOG = WORKSPACE_ROOT / "logs" / "dashboard_ui_debug.jsonl"


def _log_ui_debug(event: str, data: dict[str, Any]) -> None:
    entry = {
        "ts": datetime.now(HKT_TZ).isoformat(),
        "event": event,
        "data": data,
    }
    try:
        UI_DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with UI_DEBUG_LOG.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _card_html(
    item: dict[str, Any],
    dt_hkt: datetime,
    schedule_item_id: str = "",
    lock_schedule_key: str = "",
    unschedule_key: str = "",
    edit_action_key: str = "",
    delete_action_key: str = "",
    is_locked: bool = False,
) -> str:
    link = escape(str(item.get("Post URL", "#")))
    title = escape(str(item.get("title", "")))
    thumb = escape(resolve_thumbnail_src(str(item.get("thumbnail", ""))))
    fallback_thumb = escape(resolve_thumbnail_src("data/samples/Dummy1.png"))
    time_text = dt_hkt.strftime("%m/%d %H:%M")
    category = str(item.get("category", ""))
    category_cls = CATEGORY_CLASS_MAP.get(category, "")
    card_cls = f" post-card-{category_cls}" if category_cls else ""
    card_action_html = ""
    if schedule_item_id:
        card_action_html = (
            f'<button type="button" class="post-card-schedule-btn" data-item-id="{escape(schedule_item_id)}" '
            f'title="加入排程" aria-label="加入排程">📅</button>'
        )
        card_cls += " post-card-has-schedule"
    elif lock_schedule_key:
        lock_state_cls = " is-locked" if is_locked else ""
        lock_title = "取消锁定该时间窗口" if is_locked else "锁定该时间窗口"
        lock_html = (
            f'<button type="button" class="post-card-lock-btn{lock_state_cls}" data-schedule-key="{escape(lock_schedule_key)}" '
            f'title="{escape(lock_title)}" aria-label="{escape(lock_title)}">'
            f'<svg class="post-card-lock-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            f'<path d="M17 10h-1V7a4 4 0 0 0-8 0v3H7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zm-6 6.73V18a1 1 0 0 0 2 0v-1.27a2 2 0 1 0-2 0zM10 10V7a2 2 0 0 1 4 0v3h-4z"></path>'
            f"</svg>"
            f"</button>"
        )
        unschedule_html = ""
        if unschedule_key:
            unschedule_html = (
                f'<button type="button" class="post-card-return-btn" data-unschedule-key="{escape(unschedule_key)}" '
                f'title="取消排程并返回已出未排" aria-label="取消排程并返回已出未排">🔙</button>'
            )
        card_action_html = lock_html + unschedule_html
        card_cls += " post-card-has-schedule"
    side_actions_html = ""
    if edit_action_key:
        side_actions_html += (
            f'<button type="button" class="post-card-side-btn post-card-edit-btn" data-edit-key="{escape(edit_action_key)}" '
            f'title="修改貼文" aria-label="修改貼文">✏️</button>'
        )
    if delete_action_key:
        side_actions_html += (
            f'<button type="button" class="post-card-side-btn post-card-delete-btn" data-delete-key="{escape(delete_action_key)}" '
            f'title="刪除貼文" aria-label="刪除貼文">🗑️</button>'
        )
    if side_actions_html:
        card_action_html += f'<div class="post-card-side-actions">{side_actions_html}</div>'
        card_cls += " post-card-has-side-actions"
    if thumb:
        thumb_html = (
            '<div class="post-thumb-wrap">'
            f'<img class="post-thumb" src="{thumb}" alt="thumbnail" '
            f'onerror="this.onerror=null;this.src=\'{fallback_thumb}\';"/>'
            "</div>"
        )
    else:
        thumb_html = (
            '<div class="post-thumb-wrap">'
            f'<img class="post-thumb" src="{fallback_thumb}" alt="thumbnail"/>'
            "</div>"
        )
    return (
        f'<div class="post-card{card_cls}">'
        f"{card_action_html}"
        f'<a class="post-card-link" href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<div class="post-time">{time_text}</div>'
        f"{thumb_html}"
        f'<div class="post-title">{title}</div>'
        "</a>"
        "</div>"
    )


def _collect_time_sorted_items(items: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    collected: list[tuple[datetime, dict[str, Any]]] = []
    for item in items:
        dt = parse_publish_time(str(item.get("publish_time", "")))
        if dt is not None:
            collected.append((dt, item))
    return collected


def _build_action_key(item: dict[str, Any]) -> str:
    post_link_id = str(item.get("post_link_id", "")).strip()
    if post_link_id:
        return f"plink:{post_link_id}"
    post_id = str(item.get("post_id", "")).strip()
    post_url = str(item.get("Post URL", "")).strip()
    publish_time = str(item.get("publish_time", "")).strip()
    title = str(item.get("title", "")).strip()
    return f"pid:{post_id}|url:{post_url}|time:{publish_time}|title:{title}"


def _safe_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def _extract_action_ids(item: dict[str, Any]) -> tuple[int, str]:
    post_id = _safe_int(item.get("post_id", 0))
    if post_id <= 0:
        post_id = _safe_int(item.get("item_id", 0))
    post_link_id = str(item.get("post_link_id", "")).strip()
    if post_id <= 0:
        post_url = str(item.get("Post URL", "")).strip()
        if "permalink.php" in post_url:
            try:
                from urllib import parse as urlparse

                parsed = urlparse.urlsplit(post_url)
                query = urlparse.parse_qs(parsed.query)
                post_id = _safe_int((query.get("id") or [""])[0])
                story_fbid = str((query.get("story_fbid") or [""])[0]).strip()
                if not post_link_id and post_id > 0 and story_fbid:
                    post_link_id = f"{post_id}_{story_fbid}"
            except Exception:
                pass
    return post_id, post_link_id


def _to_hkt_input_time(dt_hkt: datetime) -> str:
    return dt_hkt.strftime("%Y-%m-%dT%H:%M")


def _refresh_board_from_api() -> tuple[bool, str]:
    sync_live_data_to_sample_files.clear()
    result = sync_live_data_to_sample_files(
        enable_category_alias_mode=bool(st.session_state.get("cfg_enable_category_alias_mode", False)),
        target_fan_page_id=str(st.session_state.get("cfg_target_fan_page_id", "350584865140118")).strip(),
    )
    if result.get("ok"):
        return True, (
            "已刷新："
            f"已發佈 {int(result.get('published_count', 0))} / "
            f"已排程 {int(result.get('scheduled_count', 0))} / "
            f"已出未排 {int(result.get('pending_count', 0))}"
        )
    return False, f"操作成功，但同步最新数据失败：{result.get('message', 'unknown')}"


def _close_all_dialog_flags() -> None:
    st.session_state["schedule_dialog_open"] = False
    st.session_state["schedule_pick_item_id"] = ""
    st.session_state["update_dialog_open"] = False
    st.session_state["update_pick_key"] = ""
    st.session_state["update_pick_mode"] = ""
    st.session_state["delete_dialog_open"] = False
    st.session_state["delete_pick_key"] = ""
    st.session_state["delete_dialog_mode"] = ""


def _validate_update_time_and_window(
    *,
    picked_dt: datetime,
    now_hkt: datetime,
    window_minutes: int,
    scheduled_items: list[tuple[datetime, dict[str, Any]]],
    target_action_key: str,
) -> tuple[bool, str]:
    step = int(window_minutes) if int(window_minutes) > 0 else DEFAULT_SCHEDULE_WINDOW_MINUTES
    if picked_dt.minute % step != 0:
        return False, f"时间必须符合 {step} 分钟窗口。"
    if picked_dt <= now_hkt.replace(second=0, microsecond=0):
        return False, "不能设置过去时间，请选择当前之后的时间窗口。"
    picked_slot = picked_dt.replace(second=0, microsecond=0)
    for dt, row in scheduled_items:
        if _build_action_key(row) == target_action_key:
            continue
        if bool(row.get("is_locked", False)) and dt.replace(second=0, microsecond=0) == picked_slot:
            return False, "该时间窗口已锁定，不能修改到这个时间。"
    return True, ""


def _process_pending_fb_action(scheduled_items: list[tuple[datetime, dict[str, Any]]], now_hkt: datetime) -> None:
    action_payload = st.session_state.get("pending_fb_action")
    if not isinstance(action_payload, dict) or not action_payload:
        return
    if not bool(action_payload.get("_started", False)):
        action_payload["_started"] = True
        st.session_state["pending_fb_action"] = action_payload
        st.session_state["_pending_action_needs_kick"] = True
        _log_ui_debug(
            "pending_action_stage_prepared",
            {"action_type": str(action_payload.get("type", "")), "kick_needed": True},
        )
        st.rerun()
    action_type = str(action_payload.get("type", "")).strip()
    _log_ui_debug("pending_action_execute_started", {"action_type": action_type})
    client = FBActionClient()
    st.session_state["fb_action_busy"] = True
    result: dict[str, Any]
    with st.spinner("正在与 FB API 通信，请稍候..."):
        if action_type == "publish":
            result = client.publish_post(
                post_id=int(action_payload.get("post_id", 0)),
                post_message=str(action_payload.get("post_message", "")).strip(),
                post_link_time=str(action_payload.get("post_link_time", "")).strip(),
                post_link_type=str(action_payload.get("post_link_type", "link")).strip(),
                image_url=str(action_payload.get("image_url", "")).strip(),
                post_mp4_url=str(action_payload.get("post_mp4_url", "")).strip(),
                post_timezone="Asia/Hong_Kong",
            )
        elif action_type == "update":
            picked_time = str(action_payload.get("post_link_time", "")).strip()
            enforce_window = bool(action_payload.get("enforce_time_validation", False))
            if enforce_window:
                try:
                    picked_dt = datetime.strptime(picked_time, "%Y-%m-%dT%H:%M").replace(tzinfo=HKT_TZ)
                except ValueError:
                    result = {"ok": False, "message": "时间格式错误，请使用 YYYY-MM-DDTHH:mm。", "log_file": "N/A"}
                else:
                    ok_time, msg_time = _validate_update_time_and_window(
                        picked_dt=picked_dt,
                        now_hkt=now_hkt,
                        window_minutes=int(st.session_state.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
                        scheduled_items=scheduled_items,
                        target_action_key=str(action_payload.get("target_action_key", "")).strip(),
                    )
                    if not ok_time:
                        result = {"ok": False, "message": msg_time, "log_file": "N/A"}
                    else:
                        result = client.update_post(
                            post_id=int(action_payload.get("post_id", 0)),
                            post_link_id=str(action_payload.get("post_link_id", "")).strip(),
                            post_message=str(action_payload.get("post_message", "")).strip(),
                            post_link_time=picked_time,
                            post_link_type=str(action_payload.get("post_link_type", "link")).strip(),
                            image_url=str(action_payload.get("image_url", "")).strip(),
                            post_mp4_url=str(action_payload.get("post_mp4_url", "")).strip(),
                        )
            else:
                result = client.update_post(
                    post_id=int(action_payload.get("post_id", 0)),
                    post_link_id=str(action_payload.get("post_link_id", "")).strip(),
                    post_message=str(action_payload.get("post_message", "")).strip(),
                    post_link_time=picked_time,
                    post_link_type=str(action_payload.get("post_link_type", "link")).strip(),
                    image_url=str(action_payload.get("image_url", "")).strip(),
                    post_mp4_url=str(action_payload.get("post_mp4_url", "")).strip(),
                )
        elif action_type == "delete":
            result = client.delete_post(
                post_id=int(action_payload.get("post_id", 0)),
                post_link_id=str(action_payload.get("post_link_id", "")).strip(),
            )
        else:
            result = {"ok": False, "message": f"未知动作：{action_type}", "log_file": "N/A"}
    st.session_state["fb_action_busy"] = False
    st.session_state["pending_fb_action"] = {}
    if result.get("ok"):
        ok_sync, sync_msg = _refresh_board_from_api()
        if ok_sync:
            st.session_state["board_flash"] = f"{str(action_payload.get('success_text', '操作成功'))}｜{sync_msg}"
        else:
            st.session_state["board_flash"] = str(action_payload.get("success_text", "操作成功"))
            st.session_state["board_warn"] = sync_msg
    else:
        st.session_state["board_warn"] = (
            f"{result.get('message', '操作失败')}（log: {result.get('log_file', 'N/A')}）"
        )
    st.rerun()


def _build_column_html(
    column_title: str,
    cards_html: list[str],
    subtitle: str = "",
    sticky_slot: int | None = None,
    toggle_id: str = "",
    toggle_icon: str = "",
    category_key: str = "",
) -> str:
    subtitle_text = escape(subtitle) if subtitle else "&nbsp;"
    subtitle_html = f'<div class="board-col-subtitle">{subtitle_text}</div>'
    sticky_cls = f" board-col-sticky board-col-sticky-{sticky_slot}" if sticky_slot is not None else ""
    sticky_key_cls = f" board-col-col{sticky_slot}" if sticky_slot in (1, 2) else ""
    category_cls = f' board-col-{CATEGORY_CLASS_MAP.get(category_key, "")}' if category_key else ""
    body_html = "".join(cards_html) if cards_html else '<div class="day-empty">暂无贴文</div>'
    if toggle_id:
        safe_icon = escape(toggle_icon or "⟷")
        head_html = (
            f'<div class="board-col-head">'
            f'<label class="col-head-toggle" for="{escape(toggle_id)}" title="点击隐藏/显示本列">'
            f'<span class="col-head-main"><span class="col-head-icon">{safe_icon}</span><span class="col-head-title">{escape(column_title)}</span></span>'
            f'<span class="col-head-hint">&lt;&lt;&lt;</span>'
            f"</label>"
            f"{subtitle_html}"
            f"</div>"
        )
    else:
        head_html = f'<div class="board-col-head">{escape(column_title)}{subtitle_html}</div>'
    return (
        f'<div class="board-col{sticky_cls}{sticky_key_cls}{category_cls}">'
        f"{head_html}"
        f'<div class="post-stack">{body_html}</div>'
        "</div>"
    )


def _render_schedule_dialog_if_needed(pending_lookup: dict[str, dict[str, Any]], now_hkt: datetime) -> None:
    if not hasattr(st, "dialog"):
        return
    if st.session_state.get("settings_open", False):
        st.session_state["schedule_dialog_open"] = False
        st.session_state["schedule_pick_item_id"] = ""
        return

    target_item_id = str(st.session_state.get("schedule_pick_item_id", "")).strip()
    is_open = bool(st.session_state.get("schedule_dialog_open", False))
    if not is_open or not target_item_id:
        return

    item = pending_lookup.get(target_item_id)
    if not item:
        st.warning("目标待排程贴文不存在，可能已处理。")
        st.session_state["schedule_dialog_open"] = False
        st.session_state["schedule_pick_item_id"] = ""
        return

    raw_window = int(st.session_state.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES))
    window_minutes = raw_window if raw_window in SCHEDULE_WINDOW_OPTIONS else DEFAULT_SCHEDULE_WINDOW_MINUTES
    default_dt = round_up_to_window(now_hkt + timedelta(minutes=window_minutes), window_minutes)
    dialog_token = int(st.session_state.get("schedule_dialog_token", 0))
    key_year = f"sched_year_{target_item_id}_{dialog_token}"
    key_month = f"sched_month_{target_item_id}_{dialog_token}"
    key_day = f"sched_day_{target_item_id}_{dialog_token}"
    key_hour = f"sched_hour_{target_item_id}_{dialog_token}"
    key_min = f"sched_min_{target_item_id}_{dialog_token}"
    st.session_state.setdefault(key_year, default_dt.year)
    st.session_state.setdefault(key_month, default_dt.month)
    st.session_state.setdefault(key_day, default_dt.day)
    st.session_state.setdefault(key_hour, default_dt.hour)
    st.session_state.setdefault(key_min, (default_dt.minute // window_minutes) * window_minutes)

    @st.dialog("设置排程时间")
    def _schedule_dialog() -> None:
        slot_list_text = "/".join([f"{x:02d}" for x in range(0, 60, window_minutes)])
        st.caption(f"点击卡片顶部日历按钮后，请设置发布时间（{window_minutes} 分钟粒度，仅 {slot_list_text}）。")
        st.write(f"目标贴文：{item.get('title', 'N/A')}")
        components.html(
            """
            <script>
            (function () {
              const blurActive = () => {
                const el = window.parent.document.activeElement;
                if (el && typeof el.blur === 'function') el.blur();
              };
              blurActive();
              window.setTimeout(blurActive, 120);
            })();
            </script>
            """,
            height=0,
            scrolling=False,
        )

        selected_year = int(st.session_state.get(key_year, default_dt.year))
        selected_month = int(st.session_state.get(key_month, default_dt.month))
        selected_day = int(st.session_state.get(key_day, default_dt.day))
        selected_max_day = calendar.monthrange(selected_year, selected_month)[1]
        if selected_day > selected_max_day:
            selected_day = selected_max_day
            st.session_state[key_day] = selected_day
        selected_date = datetime(selected_year, selected_month, selected_day, tzinfo=HKT_TZ).date()
        today = now_hkt.date()
        if selected_date < today:
            st.session_state[key_year] = today.year
            st.session_state[key_month] = today.month
            st.session_state[key_day] = today.day
            selected_year, selected_month, selected_day = today.year, today.month, today.day
            selected_date = today

        all_slots = [(h, m) for h in range(24) for m in range(0, 60, window_minutes)]
        slot_tuples = all_slots
        if selected_date == today:
            earliest_slot = round_up_to_window(now_hkt + timedelta(seconds=1), window_minutes)
            slot_tuples = [
                (h, m)
                for h, m in all_slots
                if datetime(selected_year, selected_month, selected_day, h, m, tzinfo=HKT_TZ) >= earliest_slot
            ]
        if not slot_tuples:
            next_day = today + timedelta(days=1)
            st.session_state[key_year] = next_day.year
            st.session_state[key_month] = next_day.month
            st.session_state[key_day] = next_day.day
            selected_year, selected_month, selected_day = next_day.year, next_day.month, next_day.day
            selected_date = next_day
            slot_tuples = all_slots

        hour_options = sorted({h for h, _ in slot_tuples})
        if int(st.session_state.get(key_hour, default_dt.hour)) not in hour_options:
            st.session_state[key_hour] = hour_options[0]
        minute_options = [m for h, m in slot_tuples if h == int(st.session_state.get(key_hour, hour_options[0]))]
        if int(st.session_state.get(key_min, default_dt.minute)) not in minute_options:
            st.session_state[key_min] = minute_options[0]

        hour_col, min_col = st.columns([1, 1])
        with hour_col:
            st.selectbox("小时", options=hour_options, key=key_hour, format_func=lambda x: f"{int(x):02d}")
        with min_col:
            st.selectbox(
                "分钟",
                options=[m for h, m in slot_tuples if h == int(st.session_state.get(key_hour, hour_options[0]))],
                key=key_min,
                format_func=lambda x: f"{int(x):02d}",
            )

        st.caption("日期")
        year_col, month_col, day_col = st.columns(3)
        with year_col:
            st.selectbox(
                "年",
                options=list(range(default_dt.year - 1, default_dt.year + 3)),
                key=key_year,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):04d}",
            )
        with month_col:
            st.selectbox(
                "月",
                options=list(range(1, 13)),
                key=key_month,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):02d}",
            )
        selected_year = int(st.session_state.get(key_year, default_dt.year))
        selected_month = int(st.session_state.get(key_month, default_dt.month))
        selected_max_day = calendar.monthrange(selected_year, selected_month)[1]
        current_day = int(st.session_state.get(key_day, default_dt.day))
        if current_day > selected_max_day:
            current_day = selected_max_day
            st.session_state[key_day] = current_day
        with day_col:
            st.selectbox(
                "日",
                options=list(range(1, selected_max_day + 1)),
                key=key_day,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):02d}",
            )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            is_busy = bool(st.session_state.get("fb_action_busy", False))
            if st.button("确认排程", use_container_width=True, disabled=is_busy):
                chosen_year = int(st.session_state.get(key_year, default_dt.year))
                chosen_month = int(st.session_state.get(key_month, default_dt.month))
                chosen_day = int(st.session_state.get(key_day, default_dt.day))
                chosen_hour = int(st.session_state.get(key_hour, default_dt.hour))
                chosen_min = int(st.session_state.get(key_min, default_dt.minute))
                schedule_dt = datetime(
                    chosen_year,
                    chosen_month,
                    chosen_day,
                    chosen_hour,
                    chosen_min,
                    tzinfo=HKT_TZ,
                )
                post_id = _safe_int(item.get("post_id", 0))
                if post_id <= 0:
                    post_id = _safe_int(item.get("item_id", 0))
                post_type = str(item.get("post_link_type", "link")).strip().lower() or "link"
                post_message = str(item.get("post_message", "")).strip() or str(item.get("title", "")).strip()
                image_url = str(item.get("image_url", "")).strip()
                post_mp4_url = str(item.get("post_mp4_url", "")).strip()
                if post_id <= 0:
                    st.error("缺少 post_id，无法排程发布。")
                elif post_type == "photo" and not image_url:
                    st.error("当前类型为 photo，缺少 image_url。")
                elif post_type == "video" and not post_mp4_url:
                    st.error("当前类型为 video，缺少 post_mp4_url。")
                else:
                    st.session_state["pending_fb_action"] = {
                        "type": "publish",
                        "post_id": post_id,
                        "post_message": post_message,
                        "post_link_time": _to_hkt_input_time(schedule_dt),
                        "post_link_type": post_type,
                        "image_url": image_url,
                        "post_mp4_url": post_mp4_url,
                        "success_text": f"排程成功：{schedule_dt:%Y-%m-%d %H:%M}（HKT）",
                    }
                    _close_all_dialog_flags()
                    st.rerun()
        with action_col2:
            if st.button("取消", use_container_width=True):
                st.session_state["schedule_dialog_open"] = False
                st.session_state["schedule_pick_item_id"] = ""
                st.rerun()

    _schedule_dialog()


def _render_update_dialog_if_needed(
    scheduled_lookup: dict[str, dict[str, Any]],
    published_lookup: dict[str, dict[str, Any]],
    now_hkt: datetime,
) -> None:
    if not hasattr(st, "dialog"):
        return
    target_mode = str(st.session_state.get("update_pick_mode", "")).strip()
    target_key = str(st.session_state.get("update_pick_key", "")).strip()
    if not bool(st.session_state.get("update_dialog_open", False)) or not target_key:
        return
    item_lookup = scheduled_lookup if target_mode == "scheduled" else published_lookup
    item = item_lookup.get(target_key)
    if not item:
        st.warning("目标贴文不存在，可能已更新。")
        st.session_state["update_dialog_open"] = False
        st.session_state["update_pick_key"] = ""
        return

    default_dt = parse_publish_time(str(item.get("publish_time", ""))) or now_hkt
    default_type = str(item.get("post_link_type", "link")).strip().lower() or "link"
    if default_type not in {"link", "text", "photo", "video"}:
        default_type = "link"
    default_message = str(item.get("post_message", "")).strip() or str(item.get("title", "")).strip()
    default_image_url = str(item.get("image_url", "")).strip()
    default_mp4_url = str(item.get("post_mp4_url", "")).strip()

    dialog_token = int(st.session_state.get("update_dialog_token", 0))
    key_time = f"update_time_{target_key}_{dialog_token}"
    key_year = f"update_year_{target_key}_{dialog_token}"
    key_month = f"update_month_{target_key}_{dialog_token}"
    key_day = f"update_day_{target_key}_{dialog_token}"
    key_hour = f"update_hour_{target_key}_{dialog_token}"
    key_min = f"update_min_{target_key}_{dialog_token}"
    key_type = f"update_type_{target_key}_{dialog_token}"
    key_message = f"update_message_{target_key}_{dialog_token}"
    key_image = f"update_image_{target_key}_{dialog_token}"
    key_mp4 = f"update_mp4_{target_key}_{dialog_token}"

    raw_window = int(st.session_state.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES))
    window_minutes = raw_window if raw_window in SCHEDULE_WINDOW_OPTIONS else DEFAULT_SCHEDULE_WINDOW_MINUTES
    st.session_state.setdefault(key_time, _to_hkt_input_time(default_dt))
    st.session_state.setdefault(key_year, default_dt.year)
    st.session_state.setdefault(key_month, default_dt.month)
    st.session_state.setdefault(key_day, default_dt.day)
    st.session_state.setdefault(key_hour, default_dt.hour)
    st.session_state.setdefault(key_min, (default_dt.minute // window_minutes) * window_minutes)
    st.session_state.setdefault(key_type, default_type)
    st.session_state.setdefault(key_message, default_message)
    st.session_state.setdefault(key_image, default_image_url)
    st.session_state.setdefault(key_mp4, default_mp4_url)

    @st.dialog("修改贴文")
    def _update_dialog() -> None:
        st.write(f"目标贴文：{item.get('title', 'N/A')}")
        slot_list_text = "/".join([f"{x:02d}" for x in range(0, 60, window_minutes)])
        st.caption(f"时间粒度：{window_minutes} 分钟（仅 {slot_list_text}）")

        selected_year = int(st.session_state.get(key_year, default_dt.year))
        selected_month = int(st.session_state.get(key_month, default_dt.month))
        selected_day = int(st.session_state.get(key_day, default_dt.day))
        selected_max_day = calendar.monthrange(selected_year, selected_month)[1]
        if selected_day > selected_max_day:
            selected_day = selected_max_day
            st.session_state[key_day] = selected_day
        selected_date = datetime(selected_year, selected_month, selected_day, tzinfo=HKT_TZ).date()
        today = now_hkt.date()
        if target_mode == "scheduled" and selected_date < today:
            st.session_state[key_year] = today.year
            st.session_state[key_month] = today.month
            st.session_state[key_day] = today.day
            selected_year, selected_month, selected_day = today.year, today.month, today.day
            selected_date = today

        all_slots = [(h, m) for h in range(24) for m in range(0, 60, window_minutes)]
        slot_tuples = all_slots
        if target_mode == "scheduled" and selected_date == today:
            earliest_slot = round_up_to_window(now_hkt + timedelta(seconds=1), window_minutes)
            slot_tuples = [
                (h, m)
                for h, m in all_slots
                if datetime(selected_year, selected_month, selected_day, h, m, tzinfo=HKT_TZ) >= earliest_slot
            ]
        if not slot_tuples:
            next_day = today + timedelta(days=1)
            st.session_state[key_year] = next_day.year
            st.session_state[key_month] = next_day.month
            st.session_state[key_day] = next_day.day
            selected_year, selected_month, selected_day = next_day.year, next_day.month, next_day.day
            slot_tuples = all_slots

        hour_options = sorted({h for h, _ in slot_tuples})
        if int(st.session_state.get(key_hour, default_dt.hour)) not in hour_options:
            st.session_state[key_hour] = hour_options[0]
        minute_options = [m for h, m in slot_tuples if h == int(st.session_state.get(key_hour, hour_options[0]))]
        if int(st.session_state.get(key_min, default_dt.minute)) not in minute_options:
            st.session_state[key_min] = minute_options[0]

        hour_col, min_col = st.columns([1, 1])
        with hour_col:
            st.selectbox("小时", options=hour_options, key=key_hour, format_func=lambda x: f"{int(x):02d}")
        with min_col:
            st.selectbox(
                "分钟",
                options=[m for h, m in slot_tuples if h == int(st.session_state.get(key_hour, hour_options[0]))],
                key=key_min,
                format_func=lambda x: f"{int(x):02d}",
            )

        st.caption("日期")
        year_col, month_col, day_col = st.columns(3)
        with year_col:
            st.selectbox(
                "年",
                options=list(range(default_dt.year - 1, default_dt.year + 3)),
                key=key_year,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):04d}",
            )
        with month_col:
            st.selectbox(
                "月",
                options=list(range(1, 13)),
                key=key_month,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):02d}",
            )
        selected_year = int(st.session_state.get(key_year, default_dt.year))
        selected_month = int(st.session_state.get(key_month, default_dt.month))
        selected_max_day = calendar.monthrange(selected_year, selected_month)[1]
        current_day = int(st.session_state.get(key_day, default_dt.day))
        if current_day > selected_max_day:
            current_day = selected_max_day
            st.session_state[key_day] = current_day
        with day_col:
            st.selectbox(
                "日",
                options=list(range(1, selected_max_day + 1)),
                key=key_day,
                label_visibility="collapsed",
                format_func=lambda x: f"{int(x):02d}",
            )

        picked_dt = datetime(
            int(st.session_state.get(key_year, default_dt.year)),
            int(st.session_state.get(key_month, default_dt.month)),
            int(st.session_state.get(key_day, default_dt.day)),
            int(st.session_state.get(key_hour, default_dt.hour)),
            int(st.session_state.get(key_min, default_dt.minute)),
            tzinfo=HKT_TZ,
        )
        st.session_state[key_time] = _to_hkt_input_time(picked_dt)

        st.selectbox("贴文类型", options=["link", "text", "photo", "video"], key=key_type)
        st.text_area("贴文内容", key=key_message, height=160)
        selected_type = str(st.session_state.get(key_type, "link")).strip().lower()
        if selected_type == "photo":
            st.text_input("图片 URL（必填）", key=key_image)
        elif selected_type == "video":
            st.text_input("视频 URL（必填）", key=key_mp4)
        else:
            st.text_input("图片 URL（选填）", key=key_image)
            st.text_input("视频 URL（选填）", key=key_mp4)

        col1, col2 = st.columns(2)
        with col1:
            is_busy = bool(st.session_state.get("fb_action_busy", False))
            if st.button("确认修改", use_container_width=True, disabled=is_busy):
                post_id, post_link_id = _extract_action_ids(item)
                picked_time = str(st.session_state.get(key_time, "")).strip()
                picked_type = str(st.session_state.get(key_type, "link")).strip().lower()
                picked_message = str(st.session_state.get(key_message, "")).strip()
                picked_image = str(st.session_state.get(key_image, "")).strip()
                picked_mp4 = str(st.session_state.get(key_mp4, "")).strip()
                if post_id <= 0 or not post_link_id:
                    st.error("缺少 post_id 或 post_link_id，无法修改。")
                elif not picked_message:
                    st.error("贴文内容不能为空。")
                elif picked_type == "photo" and not picked_image:
                    st.error("当前类型为 photo，图片 URL 不能为空。")
                elif picked_type == "video" and not picked_mp4:
                    st.error("当前类型为 video，视频 URL 不能为空。")
                else:
                    st.session_state["pending_fb_action"] = {
                        "type": "update",
                        "post_id": post_id,
                        "post_link_id": post_link_id,
                        "post_message": picked_message,
                        "post_link_time": picked_time,
                        "post_link_type": picked_type,
                        "image_url": picked_image,
                        "post_mp4_url": picked_mp4,
                        "target_action_key": target_key,
                        "enforce_time_validation": target_mode == "scheduled",
                        "success_text": "修改成功",
                    }
                    _close_all_dialog_flags()
                    st.rerun()
        with col2:
            if st.button("返回", use_container_width=True):
                st.session_state["update_dialog_open"] = False
                st.session_state["update_pick_key"] = ""
                st.session_state["update_pick_mode"] = ""
                st.rerun()

    _update_dialog()


def _render_delete_dialog_if_needed(
    scheduled_lookup: dict[str, dict[str, Any]],
    published_lookup: dict[str, dict[str, Any]],
) -> None:
    if not hasattr(st, "dialog"):
        return
    mode = str(st.session_state.get("delete_dialog_mode", "")).strip()
    target_key = str(st.session_state.get("delete_pick_key", "")).strip()
    if not bool(st.session_state.get("delete_dialog_open", False)) or not mode or not target_key:
        return
    lookup = scheduled_lookup if mode == "scheduled" else published_lookup
    item = lookup.get(target_key)
    if not item:
        st.warning("目标贴文不存在，可能已更新。")
        st.session_state["delete_dialog_open"] = False
        st.session_state["delete_pick_key"] = ""
        st.session_state["delete_dialog_mode"] = ""
        return

    title = str(item.get("title", "N/A")).strip() or "N/A"
    link = str(item.get("Post URL", "")).strip() or "N/A"
    schedule_text = str(item.get("publish_time", "")).strip() or "N/A"

    dialog_title = "确认删除排程" if mode == "scheduled" else "确认删除贴文"

    @st.dialog(dialog_title)
    def _delete_dialog() -> None:
        if mode == "scheduled":
            st.write(f"确认删除《{title}》的排程？")
            st.caption(f"当前排程为：{schedule_text}")
        else:
            st.write(f"确认删除《{title}》?")
            st.caption(f"贴文链接：{link}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("返回", use_container_width=True):
                st.session_state["delete_dialog_open"] = False
                st.session_state["delete_pick_key"] = ""
                st.session_state["delete_dialog_mode"] = ""
                st.rerun()
        with col2:
            is_busy = bool(st.session_state.get("fb_action_busy", False))
            if st.button("确认", use_container_width=True, disabled=is_busy):
                post_id, post_link_id = _extract_action_ids(item)
                if post_id <= 0 or not post_link_id:
                    st.error("缺少 post_id 或 post_link_id，无法删除。")
                else:
                    st.session_state["pending_fb_action"] = {
                        "type": "delete",
                        "post_id": post_id,
                        "post_link_id": post_link_id,
                        "success_text": "删除成功",
                    }
                    _close_all_dialog_flags()
                    st.rerun()

    _delete_dialog()


def render_today_board() -> None:
    now_hkt = datetime.now(HKT_TZ)
    st.session_state.setdefault("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)
    if int(st.session_state.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)) not in SCHEDULE_WINDOW_OPTIONS:
        st.session_state["schedule_window_minutes"] = DEFAULT_SCHEDULE_WINDOW_MINUTES
    st.markdown(
        """
        <style>
        .st-key-schedule_pick_commit,
        .st-key-schedule_lock_commit,
        .st-key-unschedule_commit,
        .st-key-update_pick_commit,
        .st-key-delete_pick_commit {
            display: none !important;
        }
        .st-key-pending_action_kick_commit {
            position: absolute !important;
            left: -10000px !important;
            top: auto !important;
            width: 1px !important;
            height: 1px !important;
            overflow: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.button("schedule_pick_commit", key="schedule_pick_commit")
    st.button("schedule_lock_commit", key="schedule_lock_commit")
    st.button("unschedule_commit", key="unschedule_commit")
    st.button("update_pick_commit", key="update_pick_commit")
    st.button("delete_pick_commit", key="delete_pick_commit")
    st.button("pending_action_kick_commit", key="pending_action_kick_commit")
    _log_ui_debug(
        "board_render_start",
        {
            "query_keys": sorted([str(k) for k in st.query_params.keys()]),
            "query_schedule_pick": str(st.query_params.get("schedule_pick", "")),
            "query_update_pick": str(st.query_params.get("update_pick", "")),
            "query_delete_pick": str(st.query_params.get("delete_pick", "")),
            "pending_fb_action": bool(st.session_state.get("pending_fb_action")),
            "fb_action_busy": bool(st.session_state.get("fb_action_busy", False)),
            "schedule_dialog_open": bool(st.session_state.get("schedule_dialog_open", False)),
            "schedule_pick_item_id": str(st.session_state.get("schedule_pick_item_id", "")),
        },
    )

    if bool(st.session_state.pop("_pending_action_needs_kick", False)):
        _log_ui_debug("pending_action_kick_injected", {"delay_ms": 120})
        st.caption("正在准备执行操作...")
        components.html(
            """
            <script>
            (function () {
              window.setTimeout(function () {
                try {
                  const doc = window.parent.document;
                  const btn = doc.querySelector('.st-key-pending_action_kick_commit button');
                  if (btn) {
                    btn.click();
                  }
                } catch (e) {
                  // no-op
                }
              }, 120);
            })();
            </script>
            """,
            height=0,
            scrolling=False,
        )
        return

    past_24h = now_hkt - timedelta(hours=24)
    next_24h = now_hkt + timedelta(hours=24)

    scheduled_items = _collect_time_sorted_items(load_scheduled_items())
    _process_pending_fb_action(scheduled_items=scheduled_items, now_hkt=now_hkt)

    published_items = _collect_time_sorted_items(load_published_items())
    pending_items = _collect_time_sorted_items(load_pending_base())
    pending_lookup = {str(item.get("item_id", "")): item for _, item in pending_items if str(item.get("item_id", ""))}
    published_lookup = {_build_action_key(item): item for _, item in published_items}
    scheduled_lookup = {_build_action_key(item): item for _, item in scheduled_items}

    picked_raw = st.query_params.get("schedule_pick", "")
    if isinstance(picked_raw, list):
        picked_item_id = str(picked_raw[0] if picked_raw else "").strip()
    else:
        picked_item_id = str(picked_raw).strip()
    if picked_item_id:
        _log_ui_debug(
            "schedule_pick_received",
            {
                "picked_item_id": picked_item_id,
                "exists_in_pending_lookup": picked_item_id in pending_lookup,
                "pending_lookup_size": len(pending_lookup),
            },
        )
        if picked_item_id in pending_lookup:
            st.session_state["settings_open"] = False
            last_item_id = str(st.session_state.get("schedule_pick_item_id", "")).strip()
            if not st.session_state.get("schedule_dialog_open", False) or last_item_id != picked_item_id:
                st.session_state["schedule_dialog_token"] = int(st.session_state.get("schedule_dialog_token", 0)) + 1
            st.session_state["schedule_pick_item_id"] = picked_item_id
            st.session_state["schedule_dialog_open"] = True
        else:
            st.warning("未找到排程目标，可能已被处理。")
        try:
            del st.query_params["schedule_pick"]
        except Exception:
            pass

    lock_raw = st.query_params.get("lock_toggle", "")
    if isinstance(lock_raw, list):
        lock_key = str(lock_raw[0] if lock_raw else "").strip()
    else:
        lock_key = str(lock_raw).strip()
    if lock_key:
        _log_ui_debug("lock_toggle_received", {"lock_key": lock_key})
        st.session_state["settings_open"] = False
        ok, msg = toggle_scheduled_lock(lock_key)
        if ok:
            st.session_state["board_flash"] = msg
            st.session_state["schedule_dialog_open"] = False
            st.session_state["schedule_pick_item_id"] = ""
        else:
            st.warning(msg)
        try:
            del st.query_params["lock_toggle"]
        except Exception:
            pass
        st.rerun()

    unschedule_raw = st.query_params.get("unschedule_pick", "")
    if isinstance(unschedule_raw, list):
        unschedule_key = str(unschedule_raw[0] if unschedule_raw else "").strip()
    else:
        unschedule_key = str(unschedule_raw).strip()
    if unschedule_key:
        _log_ui_debug("unschedule_pick_received", {"unschedule_key": unschedule_key})
        st.session_state["settings_open"] = False
        _close_all_dialog_flags()
        st.session_state["delete_dialog_open"] = True
        st.session_state["delete_dialog_mode"] = "scheduled"
        st.session_state["delete_pick_key"] = unschedule_key
        try:
            del st.query_params["unschedule_pick"]
        except Exception:
            pass
        st.rerun()

    update_raw = st.query_params.get("update_pick", "")
    if isinstance(update_raw, list):
        update_key = str(update_raw[0] if update_raw else "").strip()
    else:
        update_key = str(update_raw).strip()
    if update_key:
        _log_ui_debug("update_pick_received", {"update_key": update_key})
        st.session_state["settings_open"] = False
        _close_all_dialog_flags()
        st.session_state["update_dialog_token"] = int(st.session_state.get("update_dialog_token", 0)) + 1
        if ":" in update_key:
            mode, key = update_key.split(":", 1)
            st.session_state["update_pick_mode"] = mode.strip()
            st.session_state["update_pick_key"] = key.strip()
            st.session_state["update_dialog_open"] = True
        try:
            del st.query_params["update_pick"]
        except Exception:
            pass
        st.rerun()

    delete_raw = st.query_params.get("delete_pick", "")
    if isinstance(delete_raw, list):
        delete_payload = str(delete_raw[0] if delete_raw else "").strip()
    else:
        delete_payload = str(delete_raw).strip()
    if delete_payload:
        _log_ui_debug("delete_pick_received", {"delete_payload": delete_payload})
        st.session_state["settings_open"] = False
        _close_all_dialog_flags()
        if ":" in delete_payload:
            delete_mode, delete_key = delete_payload.split(":", 1)
            st.session_state["delete_dialog_mode"] = delete_mode.strip()
            st.session_state["delete_pick_key"] = delete_key.strip()
            st.session_state["delete_dialog_open"] = True
        try:
            del st.query_params["delete_pick"]
        except Exception:
            pass
        st.rerun()

    available_categories = {
        str(item.get("category", "未分類"))
        for _, item in published_items + scheduled_items
    }
    ordered_categories = [x for x in CATEGORY_ORDER if x in available_categories]
    extra_categories = sorted(x for x in available_categories if x not in ordered_categories)
    all_categories = ordered_categories + extra_categories

    filter_key = "today_board_selected_categories"
    if filter_key not in st.session_state or not st.session_state.get(filter_key):
        st.session_state[filter_key] = all_categories.copy()
    selected_categories = st.multiselect(
        "分類篩選",
        options=all_categories,
        key=filter_key,
        help="仅筛选前两列（已發佈 / 已排程）。",
    )
    impact_report = st.session_state.get("last_schedule_impact_report") or {}
    shifted_rows = impact_report.get("shifted_rows", []) if isinstance(impact_report, dict) else []
    skipped_locked_rows = impact_report.get("skipped_locked_rows", []) if isinstance(impact_report, dict) else []
    if shifted_rows or skipped_locked_rows:
        locked_times = sorted(
            {str(x.get("locked_time", "")).strip() for x in skipped_locked_rows if str(x.get("locked_time", "")).strip()}
        )
        locked_times_text = "、".join(locked_times) if locked_times else "无"
        expander_title = (
            f"排程影响：顺延 {len(shifted_rows)} 篇｜锁定跳过 {len(skipped_locked_rows)} 篇（锁定时间：{locked_times_text}）"
        )
        with st.expander(expander_title, expanded=False):
            if shifted_rows:
                st.markdown("**被顺延文章**")
                for row in shifted_rows:
                    st.write(
                        f"- {row.get('title', 'N/A')}｜{row.get('old_time', 'N/A')} -> {row.get('new_time', 'N/A')}"
                    )
            if skipped_locked_rows:
                st.markdown("**锁定跳过文章**")
                for row in skipped_locked_rows:
                    st.write(f"- {row.get('title', 'N/A')}｜锁定时间：{row.get('locked_time', 'N/A')}")
            if not shifted_rows:
                st.caption("本次排程没有触发顺延。")

    chip_color_payload = {
        key: category_style_tokens(key)["header_bg"] for key in CATEGORY_ORDER if key in all_categories
    }
    components.html(
        build_chip_color_script(json.dumps(chip_color_payload, ensure_ascii=False)),
        height=0,
        scrolling=False,
    )
    active_categories = set(selected_categories or [])
    flash_message = str(st.session_state.pop("board_flash", "")).strip()
    warn_message = str(st.session_state.pop("board_warn", "")).strip()
    if flash_message:
        st.success(flash_message)
    if warn_message:
        st.warning(warn_message)

    enable_board_fallback_mode = bool(st.session_state.get("cfg_enable_board_fallback_mode", False))

    published_in_window = [
        _card_html(
            item,
            dt,
            edit_action_key=f"published:{_build_action_key(item)}",
            delete_action_key=_build_action_key(item),
        )
        for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)
        if past_24h <= dt <= now_hkt and (not active_categories or str(item.get("category", "未分類")) in active_categories)
    ]
    if published_in_window or not enable_board_fallback_mode:
        published_cards = published_in_window
    else:
        # Fallback: if no items in last 24h, show latest published items.
        published_cards = [
            _card_html(
                item,
                dt,
                edit_action_key=f"published:{_build_action_key(item)}",
                delete_action_key=_build_action_key(item),
            )
            for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)
            if not active_categories or str(item.get("category", "未分類")) in active_categories
        ]

    scheduled_in_window = [
        _card_html(
            item,
            dt,
            lock_schedule_key=build_scheduled_key(item),
            unschedule_key=_build_action_key(item),
            edit_action_key=f"scheduled:{_build_action_key(item)}",
            is_locked=bool(item.get("is_locked", False)),
        )
        for dt, item in sorted(scheduled_items, key=lambda x: x[0])
        if now_hkt <= dt <= next_24h and (not active_categories or str(item.get("category", "未分類")) in active_categories)
    ]
    if scheduled_in_window or not enable_board_fallback_mode:
        scheduled_cards = scheduled_in_window
    else:
        # Fallback: if no items in next 24h, still show scheduled list from API.
        scheduled_cards = [
            _card_html(
                item,
                dt,
                lock_schedule_key=build_scheduled_key(item),
                unschedule_key=_build_action_key(item),
                edit_action_key=f"scheduled:{_build_action_key(item)}",
                is_locked=bool(item.get("is_locked", False)),
            )
            for dt, item in sorted(scheduled_items, key=lambda x: x[0])
            if not active_categories or str(item.get("category", "未分類")) in active_categories
        ]

    pending_by_category: dict[str, list[tuple[datetime, dict[str, Any]]]] = {c: [] for c in CATEGORY_ORDER}
    for dt, item in pending_items:
        if not enable_board_fallback_mode and not (past_24h <= dt <= now_hkt):
            continue
        category = str(item.get("category", "未分類"))
        if category in pending_by_category:
            pending_by_category[category].append((dt, item))

    for category in CATEGORY_ORDER:
        pending_by_category[category].sort(key=lambda x: x[0], reverse=True)

    st.caption(f"日期（HKT）：{now_hkt:%Y-%m-%d}｜横向滚动查看全部栏目，前两列固定。")
    category_css = []
    entertainment_cls = CATEGORY_CLASS_MAP.get("娛樂", "")
    entertainment_tokens = category_style_tokens("娛樂")
    for cat in CATEGORY_ORDER:
        cls = CATEGORY_CLASS_MAP.get(cat)
        if not cls:
            continue
        tokens = category_style_tokens(cat)
        category_css.append(
            f"""
            .board-col-{cls} .board-col-head {{
                background: {tokens['header_bg']};
                border-color: {tokens['header_border']};
            }}
            .board-col-{cls} .post-card-{cls} {{
                background: {tokens['card_bg']};
                border-color: {tokens['card_border']};
            }}
            """
        )
    category_css.append(
        f"""
        /* Display mode (current default):
           - Published/Scheduled: white cards except Entertainment
           - Pending columns: keep category colors
           Keep category class markers for future user-selectable display modes. */
        .board-col-col1 .post-card,
        .board-col-col2 .post-card {{
            background: #ffffff;
            border-color: #dcdcf6;
        }}
        .board-col-col1 .post-card-{entertainment_cls},
        .board-col-col2 .post-card-{entertainment_cls} {{
            background: {entertainment_tokens['card_bg']};
            border-color: {entertainment_tokens['card_border']};
        }}
        """
    )
    board_html = """
    <style>
    .board-scroll {
        width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        padding-bottom: 6px;
        position: relative;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior-x: contain;
    }
    .board-scroll, .board-grid, .board-col, .board-col-head, .post-card {
        box-sizing: border-box;
    }
    .board-scroll::-webkit-scrollbar { height: 8px; }
    .board-scroll::-webkit-scrollbar-thumb { background: #b9b9dc; border-radius: 999px; }
    .board-scroll::-webkit-scrollbar-track { background: #ececf8; border-radius: 999px; }
    .board-grid {
        --col-width: 220px;
        --col1-width: var(--col-width);
        --col2-width: var(--col-width);
        --grid-gap: 10px;
        --frozen-bg-light: rgba(246, 248, 255, 0.86);
        --frozen-bg-dark: rgba(20, 22, 30, 0.84);
        --frozen-divider-light: rgba(24, 24, 44, 0.10);
        --frozen-divider-dark: rgba(0, 0, 0, 0.35);
        display: grid;
        grid-template-columns: var(--col1-width) var(--col2-width) repeat(7, var(--col-width));
        min-width: calc(var(--col1-width) + var(--col2-width) + 7 * var(--col-width) + 8 * var(--grid-gap));
        gap: var(--grid-gap);
        align-items: start;
        padding-bottom: 4px;
        transition: grid-template-columns .24s ease, min-width .24s ease, gap .24s ease;
    }
    .col-toggle-state {
        position: absolute;
        opacity: 0;
        pointer-events: none;
        width: 0;
        height: 0;
    }
    .board-shell {
        display: grid;
        grid-template-columns: 40px minmax(0, 1fr);
        gap: 8px;
        align-items: start;
    }
    .board-controls {
        position: sticky;
        left: 0;
        top: 0;
        z-index: 95;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .board-control-btn {
        height: 40px;
        width: 40px;
        border-radius: 10px;
        border: 1px solid #d7d9f2;
        background: rgba(248, 249, 255, 0.96);
        color: #4e4ea8;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        user-select: none;
        font-size: 18px;
        line-height: 1;
        transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease, opacity .12s ease;
    }
    .board-control-btn:hover {
        transform: translateY(-1px);
        border-color: #8a8ade;
        box-shadow: 0 4px 12px rgba(66, 66, 140, 0.18);
    }
    .board-control-btn::after {
        content: attr(data-hide-hint);
        position: absolute;
        left: 46px;
        background: rgba(24, 26, 38, 0.88);
        color: #f2f4ff;
        font-size: 11px;
        border-radius: 6px;
        padding: 2px 6px;
        white-space: nowrap;
        opacity: 0;
        transform: translateY(-1px);
        pointer-events: none;
        transition: opacity .1s ease;
    }
    @media (hover: hover) and (pointer: fine) {
        .board-control-btn:hover::after {
            opacity: 1;
        }
    }
    @media (hover: none), (pointer: coarse) {
        .board-control-btn::after {
            display: none;
        }
    }
    .board-col {
        min-height: 140px;
        position: relative;
        overflow: visible;
        width: var(--col-width);
        min-width: var(--col-width);
        max-width: var(--col-width);
    }
    .board-col-col1 {
        width: var(--col1-width);
        min-width: var(--col1-width);
        max-width: var(--col1-width);
    }
    .board-col-col2 {
        width: var(--col2-width);
        min-width: var(--col2-width);
        max-width: var(--col2-width);
    }
    .board-col-sticky {
        position: sticky;
        z-index: 60;
        isolation: isolate;
        border-radius: 10px;
        transform: translateZ(0);
        backface-visibility: hidden;
    }
    .board-col-sticky::before {
        content: "";
        position: absolute;
        inset: -2px;
        z-index: -1;
        border-radius: 10px;
        background: rgba(246, 248, 255, 0.96);
        backdrop-filter: saturate(165%) blur(14px);
        -webkit-backdrop-filter: saturate(165%) blur(14px);
        box-shadow: 6px 0 12px rgba(20, 20, 40, 0.18);
    }
    @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
        .board-col-sticky::before {
            background: var(--background-color, #ffffff);
        }
    }
    @media (prefers-color-scheme: dark) {
        .board-col-sticky::before {
            background: rgba(20, 22, 30, 0.95);
            box-shadow: 6px 0 14px rgba(0, 0, 0, 0.52);
        }
        .board-col-head {
            border-color: #3a3a48;
            background: rgba(35, 35, 46, 0.92);
            color: #efeffa;
        }
        .board-col-subtitle { color: #c9c9da; }
        .day-empty {
            border-color: #3b3b4d;
            background: rgba(34, 34, 44, 0.7);
            color: #bbbbcb;
        }
    }
    .board-col-sticky-1 { left: 0; z-index: 82; }
    .board-col-sticky-2 { left: calc(var(--col1-width) + var(--grid-gap)); z-index: 84; }
    .board-col-sticky::after {
        content: "";
        position: absolute;
        top: -2px;
        right: calc(-1 * var(--grid-gap));
        width: var(--grid-gap);
        height: calc(100% + 4px);
        background: var(--frozen-bg-light);
        backdrop-filter: saturate(165%) blur(14px);
        -webkit-backdrop-filter: saturate(165%) blur(14px);
        border-right: 1px solid var(--frozen-divider-light);
        pointer-events: none;
    }
    .board-col-sticky-2::after {
        box-shadow: 6px 0 12px var(--frozen-divider-light);
    }
    .board-col-sticky-1::after {
        box-shadow: 4px 0 10px var(--frozen-divider-light);
    }
    @media (prefers-color-scheme: dark) {
        .board-col-sticky::after {
            background: var(--frozen-bg-dark);
            border-right-color: var(--frozen-divider-dark);
        }
        .board-col-sticky-2::after {
            box-shadow: 8px 0 14px var(--frozen-divider-dark);
        }
    }
    @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
        .board-col-sticky::after {
            background: var(--background-color, #ffffff);
        }
    }
    .board-col-head {
        position: sticky;
        top: 0;
        z-index: 31;
        border: 1px solid #d9d9ea;
        border-radius: 8px;
        background: #f8f8ff;
        color: #222;
        padding: 8px;
        font-size: 15px;
        font-weight: 700;
        line-height: 1.2;
        pointer-events: auto;
        width: 100%;
    }
    .col-head-toggle {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
        cursor: pointer;
        user-select: none;
    }
    .col-head-main {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-width: 0;
    }
    .col-head-icon {
        color: #4e4ea8;
        font-size: 16px;
        line-height: 1;
        flex-shrink: 0;
    }
    .col-head-title {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .col-head-hint {
        font-size: 11px;
        color: #7b7b95;
        flex-shrink: 0;
        letter-spacing: -0.5px;
    }
    .col-head-toggle:hover .col-head-hint {
        color: #4e4ea8;
    }
    .board-col-subtitle {
        margin-top: 4px;
        font-size: 11px;
        color: #7b7b95;
        font-weight: 500;
    }
    .board-col-col1 .board-col-subtitle,
    .board-col-col2 .board-col-subtitle {
        display: block;
        min-height: 15px;
    }
    .post-stack {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: 6px;
        margin-top: 8px;
    }
    .day-empty {
        font-size: 12px;
        color: #8b8b98;
        text-align: center;
        padding: 12px 0;
        border: 1px dashed #ddddee;
        border-radius: 8px;
        background: #fcfcff;
    }
    .post-card {
        display: block;
        position: relative;
        width: var(--col-width);
        min-width: var(--col-width);
        max-width: var(--col-width);
        border: 1px solid #dcdcf6;
        border-radius: 8px;
        overflow: visible;
        background: #fff;
        transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease, opacity .15s ease;
    }
    .post-card-link {
        display: block;
        text-decoration: none;
        color: inherit;
        border-radius: 8px;
        overflow: hidden;
    }
    .post-card-has-schedule .post-card-link {
        padding-top: 0;
    }
    .post-card-schedule-btn {
        position: absolute;
        top: 6px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 4;
        width: 22px;
        height: 22px;
        border-radius: 999px;
        border: 1px solid #d4d7f5;
        background: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(62, 62, 132, 0.12);
        line-height: 1;
        font-size: 13px;
        transition: transform .12s ease, border-color .12s ease, box-shadow .12s ease;
    }
    .post-card-lock-btn {
        position: absolute;
        top: 6px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 4;
        width: 22px;
        height: 22px;
        border-radius: 999px;
        border: 1px solid #d4d7f5;
        background: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(62, 62, 132, 0.12);
        color: #5a5ab1;
        line-height: 1;
        opacity: 0.75;
        transition: transform .12s ease, border-color .12s ease, box-shadow .12s ease, opacity .12s ease;
    }
    .post-card-lock-icon {
        width: 13px;
        height: 13px;
        display: block;
        fill: currentColor;
    }
    .post-card-return-btn {
        position: absolute;
        top: 6px;
        right: 6px;
        z-index: 4;
        width: 22px;
        height: 22px;
        border-radius: 999px;
        border: 1px solid #d4d7f5;
        background: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(62, 62, 132, 0.12);
        line-height: 1;
        font-size: 12px;
        opacity: 0.85;
        transition: transform .12s ease, border-color .12s ease, box-shadow .12s ease, opacity .12s ease;
    }
    .post-card-side-actions {
        position: absolute;
        top: 26px;
        left: -12px;
        z-index: 6;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .post-card-side-btn {
        width: 22px;
        height: 22px;
        border-radius: 999px;
        border: 1px solid #d4d7f5;
        background: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(62, 62, 132, 0.12);
        line-height: 1;
        font-size: 12px;
        opacity: 0.86;
        cursor: pointer;
        transition: transform .12s ease, border-color .12s ease, box-shadow .12s ease, opacity .12s ease;
    }
    .post-card-side-btn:hover {
        transform: translateY(-1px);
        opacity: 1;
        border-color: #8a8ade;
        box-shadow: 0 4px 10px rgba(62, 62, 132, 0.2);
    }
    .post-card-side-btn.is-loading,
    .post-card-side-btn[disabled],
    .post-card-schedule-btn.is-loading,
    .post-card-return-btn.is-loading,
    .post-card-lock-btn.is-loading {
        opacity: 0.45;
        pointer-events: none;
        cursor: not-allowed;
    }
    .post-card-lock-btn.is-locked {
        opacity: 1;
        border-color: #8a8ade;
        background: #f1efff;
        box-shadow: 0 4px 10px rgba(62, 62, 132, 0.2);
    }
    .post-card-schedule-btn:hover {
        transform: translateX(-50%) translateY(-1px);
        border-color: #8a8ade;
        box-shadow: 0 4px 10px rgba(62, 62, 132, 0.2);
    }
    .post-card-lock-btn:hover {
        transform: translateX(-50%) translateY(-1px);
        opacity: 1;
        border-color: #8a8ade;
    }
    .post-card-return-btn:hover {
        transform: translateY(-1px);
        opacity: 1;
        border-color: #8a8ade;
        box-shadow: 0 4px 10px rgba(62, 62, 132, 0.2);
    }
    .post-card:hover {
        border-color: #6e6edd;
        box-shadow: 0 4px 12px rgba(78, 78, 168, 0.18);
        transform: translateY(-1px);
        opacity: 0.96;
    }
    .post-time { font-size: 12px; color: #4e4ea8; font-weight: 600; padding: 6px 8px 0 8px; }
    .post-thumb-wrap {
        width: 200px;
        height: 150px;
        max-width: 100%;
        margin: 4px auto 0 auto;
        overflow: hidden;
        border-radius: 6px;
        background: #efeff7;
    }
    .post-thumb {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }
    .post-thumb-placeholder {
        width: 200px;
        height: 150px;
        max-width: 100%;
        margin: 4px auto 0 auto;
        background: #efeff7;
    }
    .post-title {
        font-size: 12px;
        line-height: 1.35;
        padding: 6px 8px 8px 8px;
        color: #222;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-height: 19px;
    }
    @media (max-width: 980px) {
        .board-grid {
            --col-width: 220px;
        }
        .board-col-head { font-size: 14px; }
        .board-col-subtitle { font-size: 10px; }
    }
    @media (max-width: 768px) {
        .board-grid {
            --col-width: 220px;
            --grid-gap: 8px;
        }
        .board-shell {
            grid-template-columns: 36px minmax(0, 1fr);
            gap: 6px;
        }
        .board-control-btn {
            width: 36px;
            height: 36px;
            font-size: 16px;
            border-radius: 9px;
        }
        .board-col {
            min-height: 120px;
        }
        .board-col-sticky::before {
            box-shadow: 4px 0 8px rgba(20, 20, 40, 0.10);
        }
        .board-col-sticky-2::after {
            box-shadow: 4px 0 8px var(--frozen-divider-light);
        }
        .board-col-head {
            font-size: 13px;
            padding: 7px 6px;
        }
        .col-head-icon { font-size: 14px; }
        .col-head-hint { font-size: 10px; }
        .post-stack {
            gap: 5px;
            margin-top: 6px;
        }
        .post-time {
            font-size: 11px;
            padding: 5px 6px 0 6px;
        }
        .post-card-schedule-btn {
            width: 20px;
            height: 20px;
            top: 5px;
            font-size: 12px;
        }
        .post-card-lock-btn {
            width: 20px;
            height: 20px;
            top: 5px;
        }
        .post-card-lock-icon { width: 12px; height: 12px; }
        .post-card-return-btn {
            width: 20px;
            height: 20px;
            top: 5px;
            right: 5px;
            font-size: 11px;
        }
        .post-card-side-actions {
            left: -11px;
            top: 24px;
            gap: 3px;
        }
        .post-card-side-btn {
            width: 20px;
            height: 20px;
            font-size: 11px;
        }
        .post-thumb, .post-thumb-placeholder { margin-top: 3px; }
        .post-title {
            font-size: 11px;
            line-height: 1.25;
            padding: 5px 6px 7px 6px;
            min-height: 30px;
        }
    }
    .board-root:has(#toggle-col1:checked) .board-grid {
        --col1-width: 0px;
    }
    .board-root:has(#toggle-col2:checked) .board-grid {
        --col2-width: 0px;
    }
    .board-root:has(#toggle-col1:checked) .board-col-sticky-2 {
        left: 0;
    }
    .board-col-col1,
    .board-col-col2 {
        transition: opacity .24s ease, transform .24s ease, filter .24s ease;
        transform: translateX(0);
        opacity: 1;
    }
    .board-root:has(#toggle-col1:checked) .board-col-col1 {
        opacity: 0;
        transform: translateX(-24px);
        filter: blur(1px);
        pointer-events: none;
        overflow: hidden;
    }
    .board-root:has(#toggle-col2:checked) .board-col-col2 {
        opacity: 0;
        transform: translateX(-20px);
        filter: blur(1px);
        pointer-events: none;
        overflow: hidden;
    }
    .board-root:has(#toggle-col1:checked) .board-col-col1 .board-col-head,
    .board-root:has(#toggle-col1:checked) .board-col-col1 .post-stack,
    .board-root:has(#toggle-col2:checked) .board-col-col2 .board-col-head,
    .board-root:has(#toggle-col2:checked) .board-col-col2 .post-stack {
        visibility: hidden;
    }
    .board-root:has(#toggle-col1:checked) .board-control-published {
        opacity: 0.62;
        border-color: #8a8ade;
    }
    .board-root:has(#toggle-col2:checked) .board-control-scheduled {
        opacity: 0.62;
        border-color: #8a8ade;
    }
    .board-root:has(#toggle-col1:checked) .board-control-published::after {
        content: "已發佈 >>>";
    }
    .board-root:has(#toggle-col2:checked) .board-control-scheduled::after {
        content: "已排程 >>>";
    }
    .board-root:has(#toggle-col1:checked) .board-col-col1 .board-col-head .col-head-hint,
    .board-root:has(#toggle-col2:checked) .board-col-col2 .board-col-head .col-head-hint {
        color: #4e4ea8;
    }
    @media (prefers-color-scheme: dark) {
        .board-control-btn {
            border-color: #3a3f5b;
            background: rgba(34, 38, 56, 0.95);
            color: #aab2ff;
        }
        .col-head-hint { color: #c9c9da; }
    }
    </style>
    """
    board_html += "<style>" + "\n".join(category_css) + "</style>"
    board_html += '<div class="board-root">'
    board_html += '<input type="checkbox" id="toggle-col1" class="col-toggle-state" />'
    board_html += '<input type="checkbox" id="toggle-col2" class="col-toggle-state" />'
    board_html += '<div class="board-shell">'
    board_html += (
        '<div class="board-controls">'
        '<label class="board-control-btn board-control-published" for="toggle-col1" title="显示/隐藏 已發佈 列" data-hide-hint="已發佈 <<<">📰</label>'
        '<label class="board-control-btn board-control-scheduled" for="toggle-col2" title="显示/隐藏 已排程 列" data-hide-hint="已排程 <<<">📅</label>'
        "</div>"
    )
    board_html += '<div class="board-scroll"><div class="board-grid">'
    board_html += _build_column_html("已發佈", published_cards, sticky_slot=1, toggle_id="toggle-col1", toggle_icon="📰")
    board_html += _build_column_html("已排程", scheduled_cards, sticky_slot=2, toggle_id="toggle-col2", toggle_icon="📅")
    for category in ["社會事", "大視野", "兩岸", "法庭事", "消費", "娛樂", "心韓"]:
        category_cards = [
            _card_html(item, dt, schedule_item_id=str(item.get("item_id", "")).strip())
            for dt, item in pending_by_category.get(category, [])
        ]
        board_html += _build_column_html(category, category_cards, subtitle="已出未排", category_key=category)
    board_html += "</div></div></div></div>"
    components.html(
        textwrap.dedent(board_html) + build_schedule_pick_script(),
        height=1700,
        scrolling=True,
    )
    if bool(st.session_state.get("schedule_dialog_open", False)):
        _render_schedule_dialog_if_needed(pending_lookup=pending_lookup, now_hkt=now_hkt)
    elif bool(st.session_state.get("update_dialog_open", False)):
        _render_update_dialog_if_needed(
            scheduled_lookup=scheduled_lookup,
            published_lookup=published_lookup,
            now_hkt=now_hkt,
        )
    elif bool(st.session_state.get("delete_dialog_open", False)):
        _render_delete_dialog_if_needed(
            scheduled_lookup=scheduled_lookup,
            published_lookup=published_lookup,
        )
