from __future__ import annotations

import json
from datetime import datetime, timedelta
from html import escape
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.dashboard.config import CATEGORY_CLASS_MAP, CATEGORY_ORDER, HKT_TZ
from src.dashboard.data_utils import load_pending_base, load_published_items, load_scheduled_items
from src.dashboard.frontend_templates import build_chip_color_script, build_drag_drop_script
from src.dashboard.media_utils import parse_publish_time, resolve_thumbnail_src, round_up_to_5_minutes
from src.dashboard.scheduling_utils import move_pending_item_to_scheduled
from src.dashboard.style_utils import category_style_tokens


def _card_html(item: dict[str, Any], dt_hkt: datetime, draggable: bool = False) -> str:
    link = escape(str(item.get("Post URL", "#")))
    title = escape(str(item.get("title", "")))
    thumb = escape(resolve_thumbnail_src(str(item.get("thumbnail", ""))))
    time_text = dt_hkt.strftime("%m/%d %H:%M")
    category = str(item.get("category", ""))
    category_cls = CATEGORY_CLASS_MAP.get(category, "")
    card_cls = f" post-card-{category_cls}" if category_cls else ""
    item_id = escape(str(item.get("item_id", "")))
    drag_attrs = ""
    if draggable and item_id:
        card_cls += " post-card-draggable"
        drag_attrs = f' draggable="true" data-item-id="{item_id}"'
    if thumb:
        thumb_html = f'<img class="post-thumb" src="{thumb}" alt="thumbnail"/>'
    else:
        thumb_html = '<div class="post-thumb-placeholder"></div>'
    return (
        f'<a class="post-card{card_cls}"{drag_attrs} href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<div class="post-time">{time_text}</div>'
        f"{thumb_html}"
        f'<div class="post-title">{title}</div>'
        "</a>"
    )


def _collect_time_sorted_items(items: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    collected: list[tuple[datetime, dict[str, Any]]] = []
    for item in items:
        dt = parse_publish_time(str(item.get("publish_time", "")))
        if dt is not None:
            collected.append((dt, item))
    return collected


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

    default_dt = round_up_to_5_minutes(now_hkt + timedelta(minutes=5))
    key_date = f"sched_date_{target_item_id}"
    key_hour = f"sched_hour_{target_item_id}"
    key_min = f"sched_min_{target_item_id}"
    st.session_state.setdefault(key_date, default_dt.date())
    st.session_state.setdefault(key_hour, default_dt.hour)
    st.session_state.setdefault(key_min, (default_dt.minute // 5) * 5)

    @st.dialog("设置排程时间")
    def _schedule_dialog() -> None:
        st.caption("拖放完成后，请设置发布时间（5 分钟粒度）。")
        st.write(f"目标贴文：{item.get('title', 'N/A')}")

        date_col, hour_col, min_col = st.columns([2.2, 1, 1])
        with date_col:
            st.date_input("日期", key=key_date)
        with hour_col:
            st.selectbox("小时", options=list(range(24)), key=key_hour, format_func=lambda x: f"{int(x):02d}")
        with min_col:
            st.selectbox("分钟", options=list(range(0, 60, 5)), key=key_min, format_func=lambda x: f"{int(x):02d}")

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("确认排程", use_container_width=True):
                chosen_date = st.session_state.get(key_date, default_dt.date())
                chosen_hour = int(st.session_state.get(key_hour, default_dt.hour))
                chosen_min = int(st.session_state.get(key_min, default_dt.minute))
                schedule_dt = datetime(
                    chosen_date.year,
                    chosen_date.month,
                    chosen_date.day,
                    chosen_hour,
                    chosen_min,
                    tzinfo=HKT_TZ,
                )
                ok, msg = move_pending_item_to_scheduled(target_item_id, schedule_dt)
                if ok:
                    st.session_state["board_flash"] = f"排程成功：{schedule_dt:%Y-%m-%d %H:%M}（HKT）"
                    st.session_state["schedule_dialog_open"] = False
                    st.session_state["schedule_pick_item_id"] = ""
                    st.rerun()
                st.error(msg)
        with action_col2:
            if st.button("取消", use_container_width=True):
                st.session_state["schedule_dialog_open"] = False
                st.session_state["schedule_pick_item_id"] = ""
                st.rerun()

    _schedule_dialog()


def render_today_board() -> None:
    now_hkt = datetime.now(HKT_TZ)
    st.markdown(
        """
        <style>
        .st-key-drag_drop_commit {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.button("drag_drop_commit", key="drag_drop_commit")

    past_24h = now_hkt - timedelta(hours=24)
    next_24h = now_hkt + timedelta(hours=24)

    published_items = _collect_time_sorted_items(load_published_items())
    scheduled_items = _collect_time_sorted_items(load_scheduled_items())
    pending_items = _collect_time_sorted_items(load_pending_base())
    pending_lookup = {str(item.get("item_id", "")): item for _, item in pending_items if str(item.get("item_id", ""))}

    picked_raw = st.query_params.get("schedule_pick", "")
    if isinstance(picked_raw, list):
        picked_item_id = str(picked_raw[0] if picked_raw else "").strip()
    else:
        picked_item_id = str(picked_raw).strip()
    if st.session_state.get("debug_drag_enabled", True):
        st.caption(f"[debug] schedule_pick raw={picked_raw!r}, parsed={picked_item_id!r}")
    if picked_item_id:
        if picked_item_id in pending_lookup:
            st.session_state["schedule_pick_item_id"] = picked_item_id
            st.session_state["schedule_dialog_open"] = True
        else:
            st.warning("未找到拖放目标，可能已被处理。")
        try:
            del st.query_params["schedule_pick"]
        except Exception:
            pass

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
    if flash_message:
        st.success(flash_message)

    published_cards = [
        _card_html(item, dt, draggable=False)
        for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)
        if past_24h <= dt <= now_hkt and (not active_categories or str(item.get("category", "未分類")) in active_categories)
    ]
    scheduled_cards = [
        _card_html(item, dt, draggable=False)
        for dt, item in sorted(scheduled_items, key=lambda x: x[0])
        if now_hkt <= dt <= next_24h and (not active_categories or str(item.get("category", "未分類")) in active_categories)
    ]

    pending_by_category: dict[str, list[tuple[datetime, dict[str, Any]]]] = {c: [] for c in CATEGORY_ORDER}
    for dt, item in pending_items:
        if not (past_24h <= dt <= now_hkt):
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
        --col-width: 210px;
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
        width: 100%;
        max-width: 100%;
        border: 1px solid #dcdcf6;
        border-radius: 8px;
        overflow: hidden;
        text-decoration: none;
        color: inherit;
        background: #fff;
        transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease, opacity .15s ease;
        cursor: pointer;
    }
    .post-card-draggable {
        cursor: grab;
    }
    .post-card-draggable:active {
        cursor: grabbing;
    }
    .dropzone-active {
        outline: 2px dashed #6e6edd;
        outline-offset: 3px;
    }
    .post-card:hover {
        border-color: #6e6edd;
        box-shadow: 0 4px 12px rgba(78, 78, 168, 0.18);
        transform: translateY(-1px);
        opacity: 0.96;
    }
    .post-time { font-size: 12px; color: #4e4ea8; font-weight: 600; padding: 6px 8px 0 8px; }
    .post-thumb { width: 100%; height: 80px; object-fit: cover; display: block; margin-top: 4px; }
    .post-thumb-placeholder { width: 100%; height: 80px; margin-top: 4px; background: #efeff7; }
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
            --col-width: 180px;
        }
        .board-col-head { font-size: 14px; }
        .board-col-subtitle { font-size: 10px; }
    }
    @media (max-width: 768px) {
        .board-grid {
            --col-width: 168px;
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
        .post-thumb, .post-thumb-placeholder {
            height: 58px;
            margin-top: 3px;
        }
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
        category_cards = [_card_html(item, dt, draggable=True) for dt, item in pending_by_category.get(category, [])]
        board_html += _build_column_html(category, category_cards, subtitle="已出未排", category_key=category)
    board_html += "</div></div></div></div>"
    st.markdown(board_html, unsafe_allow_html=True)
    components.html(
        build_drag_drop_script(),
        height=0,
        scrolling=False,
    )
    _render_schedule_dialog_if_needed(pending_lookup=pending_lookup, now_hkt=now_hkt)
