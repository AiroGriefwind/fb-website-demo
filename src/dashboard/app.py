from __future__ import annotations

import json
import os
import sys
import base64
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

import streamlit as st

# Ensure imports like `from src...` work when launched via `streamlit run src/dashboard/app.py`.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.bot.review_bot import (
    TelegramAPIError,
    get_bot_profile,
    send_review_message,
    send_text_message,
)
from src.common.contracts.review_events import ReviewEvent

SAMPLES_DIR = WORKSPACE_ROOT / "data" / "samples"
RUNTIME_DIR = WORKSPACE_ROOT / "data" / "runtime"
EVENTS_FILE = RUNTIME_DIR / "review_events.jsonl"
PENDING_RUNTIME_FILE = RUNTIME_DIR / "dashboard_pending_runtime.json"

PUBLISHED_FILE = SAMPLES_DIR / "dashboard_published.json"
SCHEDULED_FILE = SAMPLES_DIR / "dashboard_scheduled.json"
PENDING_FILE = SAMPLES_DIR / "dashboard_pending.json"
TRENDS_FILE = SAMPLES_DIR / "google_trends_hk_mock.json"
DUMMY_THUMB_FILE = SAMPLES_DIR / "Dummy1.png"

API_BASE_URL_ENV = "DASHBOARD_API_BASE_URL"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"

CATEGORY_ORDER = ["娛樂", "社會事", "大視野", "兩岸", "法庭事", "消費", "心韓"]


def get_dashboard_health() -> dict[str, str]:
    return {"status": "ok", "module": "dashboard"}


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    return []


def _load_from_api(dataset: str) -> list[dict[str, Any]] | None:
    base_url = os.getenv(API_BASE_URL_ENV, "").strip()
    if not base_url:
        return None

    url = f"{base_url.rstrip('/')}/{dataset.lstrip('/')}"
    try:
        with urllib_request.urlopen(url, timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if isinstance(payload, list):
            return payload
    except (OSError, ValueError, urllib_error.URLError):
        return None
    return None


def _load_dataset(dataset: str, fallback_path: Path) -> list[dict[str, Any]]:
    api_data = _load_from_api(dataset)
    if api_data is not None:
        return api_data
    return _read_json_list(fallback_path)


def _load_published_items() -> list[dict[str, Any]]:
    return _load_dataset("published", PUBLISHED_FILE)


def _load_scheduled_items() -> list[dict[str, Any]]:
    return _load_dataset("scheduled", SCHEDULED_FILE)


def _load_pending_base() -> list[dict[str, Any]]:
    pending = _load_dataset("pending", PENDING_FILE)
    for item in pending:
        item.setdefault("review_status", ReviewEvent.WAITING.value)
        item.setdefault("updated_at", _utc_now())
    return pending


def _load_trending_keywords() -> list[dict[str, Any]]:
    return _load_dataset("trends", TRENDS_FILE)


def _write_pending_runtime(pending_items: list[dict[str, Any]]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_RUNTIME_FILE.write_text(json.dumps(pending_items, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_pending_working_set() -> list[dict[str, Any]]:
    source = _load_pending_base()
    if not PENDING_RUNTIME_FILE.exists():
        _write_pending_runtime(source)
        return source

    current = _read_json_list(PENDING_RUNTIME_FILE)
    if not current:
        _write_pending_runtime(source)
        return source

    source_by_id = {x.get("item_id"): x for x in source if x.get("item_id")}
    merged: list[dict[str, Any]] = []
    for item in current:
        item_id = item.get("item_id")
        if item_id in source_by_id:
            base = source_by_id[item_id]
            merged.append({**base, **item})
        else:
            merged.append(item)
    seen = {x.get("item_id") for x in merged}
    for item in source:
        if item.get("item_id") not in seen:
            merged.append(item)
    _write_pending_runtime(merged)
    return merged


def _append_review_event(item: dict[str, Any], event: ReviewEvent) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": _utc_now(),
        "item_id": item.get("item_id"),
        "run_id": item.get("run_id"),
        "event": event.value,
        "title": item.get("title", ""),
        "category": item.get("category", ""),
        "operator": "streamlit_ui",
    }
    with EVENTS_FILE.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _init_settings_state() -> None:
    st.session_state.setdefault("cfg_token", os.getenv(TOKEN_ENV, ""))
    st.session_state.setdefault("cfg_chat_id", os.getenv(CHAT_ID_ENV, ""))
    st.session_state.setdefault("settings_open", False)


def _render_settings_content() -> None:
    st.caption("设置 Bot Token 和 Chat ID，并测试 Telegram 连通性。")
    st.text_input("Bot Token", key="cfg_token", type="password")
    st.text_input("Chat ID", key="cfg_chat_id")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("验证 token", use_container_width=True):
            try:
                profile = get_bot_profile(st.session_state.get("cfg_token", ""))
                st.success(f"连通成功: @{profile.get('username', 'unknown')}")
            except (ValueError, TelegramAPIError, OSError) as exc:
                st.error(f"验证失败: {exc}")
    with col_b:
        if st.button("发送测试消息", use_container_width=True):
            token = st.session_state.get("cfg_token", "")
            chat_id = st.session_state.get("cfg_chat_id", "")
            if not token or not chat_id:
                st.warning("请先填写 Bot Token 和 Chat ID。")
            else:
                try:
                    result = send_text_message(
                        token=token,
                        chat_id=chat_id,
                        text="主頁FB排程控制台联通测试成功。",
                    )
                    st.success(f"发送成功，message_id={result.message_id}")
                except (ValueError, TelegramAPIError, OSError) as exc:
                    st.error(f"发送失败: {exc}")


def _render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Google Trends（香港）")
        st.markdown(
            """
            <style>
            .trend-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid #e1e1f4;
                border-radius: 8px;
                padding: 6px 10px;
                margin-bottom: 6px;
                background: #fcfcff;
                gap: 8px;
            }
            .trend-keyword {
                color: #2b2b35;
                font-size: 13px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .trend-volume {
                color: #5a5ab1;
                font-weight: 600;
                font-size: 12px;
                flex-shrink: 0;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        trends = _load_trending_keywords()
        if trends:
            for idx, item in enumerate(trends[:12], start=1):
                keyword = escape(str(item.get("keyword", "")))
                search_volume = escape(str(item.get("search_volume", "")))
                st.markdown(
                    (
                        '<div class="trend-row">'
                        f'<div class="trend-keyword">{idx}. {keyword}</div>'
                        f'<div class="trend-volume">{search_volume}</div>'
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.caption("暂无热门词数据。")

        st.divider()
        if st.button("設置", use_container_width=True):
            st.session_state["settings_open"] = True

        if st.button("重置待排程（樣本）", use_container_width=True):
            _write_pending_runtime(_load_pending_base())
            st.success("待排程列表已重置。")
            st.rerun()

        if not hasattr(st, "dialog"):
            with st.expander("設置", expanded=st.session_state.get("settings_open", False)):
                _render_settings_content()


def _render_settings_dialog_if_needed() -> None:
    if not hasattr(st, "dialog"):
        return

    @st.dialog("設置")
    def _settings_dialog() -> None:
        _render_settings_content()
        if st.button("關閉", use_container_width=True):
            st.session_state["settings_open"] = False
            st.rerun()

    if st.session_state.get("settings_open", False):
        _settings_dialog()


def _render_posts_table(items: list[dict[str, Any]], empty_text: str) -> None:
    if not items:
        st.info(empty_text)
        return
    rows = []
    for item in items:
        rows.append(
            {
                "标题": item.get("title", ""),
                "缩略图": item.get("thumbnail", ""),
                "Post URL": item.get("Post URL", ""),
                "发布时间": item.get("publish_time", ""),
                "热门词命中数": item.get("popular_count", 0),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


@st.cache_data(show_spinner=False)
def _file_to_data_uri(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists() or not path.is_file():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _resolve_thumbnail_src(raw_thumbnail: str) -> str:
    raw = (raw_thumbnail or "").strip()
    if raw.startswith(("http://", "https://", "data:")):
        return raw

    if raw:
        raw_path = Path(raw)
        if not raw_path.is_absolute():
            raw_path = WORKSPACE_ROOT / raw_path
        data_uri = _file_to_data_uri(str(raw_path))
        if data_uri:
            return data_uri

    return _file_to_data_uri(str(DUMMY_THUMB_FILE))


def _parse_publish_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _render_week_view(items: list[dict[str, Any]], key_prefix: str, empty_text: str) -> None:
    if not items:
        st.info(empty_text)
        return

    state_key = f"{key_prefix}_week_offset"
    st.session_state.setdefault(state_key, 0)

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=st.session_state[state_key] * 7)
    week_days = [start_of_week + timedelta(days=i) for i in range(7)]

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("« 往前七天", key=f"{key_prefix}_prev_week", use_container_width=True):
            st.session_state[state_key] -= 1
            st.rerun()
    with nav2:
        st.markdown(
            f"<div style='text-align:center;font-weight:600;padding-top:0.4rem;'>{week_days[0]:%m月%d日} 至 {week_days[-1]:%m月%d日}</div>",
            unsafe_allow_html=True,
        )
    with nav3:
        if st.button("往后七天 »", key=f"{key_prefix}_next_week", use_container_width=True):
            st.session_state[state_key] += 1
            st.rerun()

    day_posts: dict[int, list[tuple[datetime, dict[str, Any]]]] = {i: [] for i in range(7)}
    for item in items:
        dt = _parse_publish_time(str(item.get("publish_time", "")))
        if dt is None:
            continue
        item_day = dt.date()
        if item_day < week_days[0] or item_day > week_days[-1]:
            continue
        day_idx = (item_day - week_days[0]).days
        day_posts[day_idx].append((dt, item))

    for day_idx in day_posts:
        day_posts[day_idx].sort(key=lambda x: x[0])

    weekday_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    board_html = """
    <style>
    .week-board { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 10px; align-items: start; }
    .day-col { min-width: 0; }
    .day-head { text-align: center; font-size: 13px; color: #444; font-weight: 600; margin-bottom: 8px; padding: 6px 2px; }
    .post-stack { display: flex; flex-direction: column; gap: 6px; }
    .day-empty { font-size: 12px; color: #8b8b98; text-align: center; padding: 8px 0; }
    .post-card {
        display: block;
        border: 1px solid #dcdcf6;
        border-radius: 8px;
        overflow: hidden;
        text-decoration: none;
        color: inherit;
        background: #fff;
        transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease, opacity .15s ease;
        cursor: pointer;
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
    .post-title { font-size: 12px; line-height: 1.35; padding: 6px 8px 8px 8px; color: #222; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; min-height: 34px; }
    </style>
    """
    board_html += '<div class="week-board">'
    for day_idx, day in enumerate(week_days):
        cards = day_posts.get(day_idx, [])
        board_html += (
            '<div class="day-col">'
            f'<div class="day-head">{weekday_labels[day_idx]}<br>{day:%m月%d日}</div>'
            '<div class="post-stack">'
        )
        if not cards:
            board_html += '<div class="day-empty">暂无贴文</div>'
        for dt, item in cards:
            link = escape(str(item.get("Post URL", "#")))
            title = escape(str(item.get("title", "")))
            thumb = escape(_resolve_thumbnail_src(str(item.get("thumbnail", ""))))
            time_text = dt.strftime("%H:%M")
            if thumb:
                thumb_html = f'<img class="post-thumb" src="{thumb}" alt="thumbnail"/>'
            else:
                thumb_html = '<div class="post-thumb-placeholder"></div>'
            board_html += (
                f'<a class="post-card" href="{link}" target="_blank" rel="noopener noreferrer">'
                f'<div class="post-time">{time_text}</div>'
                f"{thumb_html}"
                f'<div class="post-title">{title}</div>'
                "</a>"
            )
        board_html += "</div></div>"
    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)


def _render_pending_item(item: dict[str, Any], category: str) -> bool:
    item_id = item.get("item_id", "unknown")
    changed = False
    status = item.get("review_status", ReviewEvent.WAITING.value)
    status_map = {
        ReviewEvent.WAITING.value: "待排程",
        ReviewEvent.APPROVED.value: "已通过",
        ReviewEvent.REJECTED.value: "已否决",
    }

    with st.expander(f"{item_id} | {item.get('title', '')[:36]}"):
        st.write(
            {
                "category": category,
                "title": item.get("title", ""),
                "Post URL": item.get("Post URL", ""),
                "publish_time": item.get("publish_time", ""),
                "popular_count": item.get("popular_count", 0),
                "status": status_map.get(status, status),
                "updated_at": item.get("updated_at", ""),
            }
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("通过", key=f"approve-{category}-{item_id}", use_container_width=True):
                item["review_status"] = ReviewEvent.APPROVED.value
                item["updated_at"] = _utc_now()
                _append_review_event(item, ReviewEvent.APPROVED)
                changed = True
        with c2:
            if st.button("否决", key=f"reject-{category}-{item_id}", use_container_width=True):
                item["review_status"] = ReviewEvent.REJECTED.value
                item["updated_at"] = _utc_now()
                _append_review_event(item, ReviewEvent.REJECTED)
                changed = True
        with c3:
            if st.button("发送到 Telegram", key=f"send-{category}-{item_id}", use_container_width=True):
                token = st.session_state.get("cfg_token", "")
                chat_id = st.session_state.get("cfg_chat_id", "")
                if not token or not chat_id:
                    st.warning("请先在設置中填写 Bot Token 和 Chat ID。")
                else:
                    try:
                        send_review_message(token=token, chat_id=chat_id, item=item)
                        st.success("待排程消息已发送到 Telegram。")
                    except (ValueError, TelegramAPIError, OSError) as exc:
                        st.error(f"发送失败: {exc}")
    return changed


def main() -> None:
    st.set_page_config(page_title="主頁FB排程", page_icon="🗂️", layout="wide")
    st.title("主頁FB排程")
    st.caption("Demo 版：已發佈 / 已排程 / 待排程，支持设置 Telegram 并执行审核流。")

    _init_settings_state()
    _render_sidebar()
    _render_settings_dialog_if_needed()

    tab_published, tab_scheduled, tab_pending = st.tabs(["已發佈", "已排程", "待排程"])

    with tab_published:
        _render_week_view(_load_published_items(), "published", "暂无已發佈数据。")

    with tab_scheduled:
        _render_week_view(_load_scheduled_items(), "scheduled", "暂无已排程数据。")

    with tab_pending:
        pending_items = _load_pending_working_set()
        waiting_count = sum(1 for x in pending_items if x.get("review_status") == ReviewEvent.WAITING.value)
        approved_count = sum(1 for x in pending_items if x.get("review_status") == ReviewEvent.APPROVED.value)
        rejected_count = sum(1 for x in pending_items if x.get("review_status") == ReviewEvent.REJECTED.value)

        m1, m2, m3 = st.columns(3)
        m1.metric("待排程", waiting_count)
        m2.metric("已通过", approved_count)
        m3.metric("已否决", rejected_count)

        changed = False
        for category in CATEGORY_ORDER:
            category_items = [x for x in pending_items if x.get("category") == category]
            with st.expander(f"{category}（{len(category_items)}）", expanded=(category == "娛樂")):
                if not category_items:
                    st.caption("暂无待审核内容。")
                    continue
                for item in category_items:
                    changed = _render_pending_item(item, category) or changed

        if changed:
            _write_pending_runtime(pending_items)
            st.rerun()


if __name__ == "__main__":
    main()

