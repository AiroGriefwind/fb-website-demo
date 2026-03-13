from __future__ import annotations

import json
import os
import sys
import base64
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from xml.etree import ElementTree as ET

import streamlit as st
import streamlit.components.v1 as components

# Ensure imports like `from src...` work when launched via `streamlit run src/dashboard/app.py`.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.bot.review_bot import (
    TelegramAPIError,
    get_bot_profile,
    send_text_message,
)

SAMPLES_DIR = WORKSPACE_ROOT / "data" / "samples"

PUBLISHED_FILE = SAMPLES_DIR / "dashboard_published.json"
SCHEDULED_FILE = SAMPLES_DIR / "dashboard_scheduled.json"
PENDING_FILE = SAMPLES_DIR / "dashboard_pending.json"
TRENDS_FILE = SAMPLES_DIR / "google_trends_hk_mock.json"
DUMMY_THUMB_FILE = SAMPLES_DIR / "Dummy1.png"

API_BASE_URL_ENV = "DASHBOARD_API_BASE_URL"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
HKT_TZ = timezone(timedelta(hours=8))
TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=HK"
TRENDS_WEB_URL = "https://trends.google.com/trending?geo=HK"
TRENDS_RSS_TTL_SECONDS = 900

CATEGORY_ORDER = ["娛樂", "社會事", "大視野", "兩岸", "法庭事", "消費", "心韓"]


def get_dashboard_health() -> dict[str, str]:
    return {"status": "ok", "module": "dashboard"}


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
    return _load_dataset("pending", PENDING_FILE)


def _load_trending_keywords() -> list[dict[str, Any]]:
    rss_data = _load_trending_keywords_from_rss()
    if rss_data:
        return rss_data
    return _load_dataset("trends", TRENDS_FILE)


@st.cache_data(show_spinner=False, ttl=TRENDS_RSS_TTL_SECONDS)
def _load_trending_keywords_from_rss() -> list[dict[str, Any]]:
    try:
        with urllib_request.urlopen(TRENDS_RSS_URL, timeout=8) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")
    except (OSError, urllib_error.URLError):
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    ns = {"ht": "https://trends.google.com/trending/rss"}
    data: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        keyword = (item.findtext("title") or "").strip()
        traffic = (item.findtext("ht:approx_traffic", namespaces=ns) or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        detail_items: list[dict[str, str]] = []
        for news in item.findall("ht:news_item", namespaces=ns):
            news_title = (news.findtext("ht:news_item_title", namespaces=ns) or "").strip()
            news_url = (news.findtext("ht:news_item_url", namespaces=ns) or "").strip()
            news_source = (news.findtext("ht:news_item_source", namespaces=ns) or "").strip()
            if news_title:
                detail_items.append({"title": news_title, "url": news_url, "source": news_source})
        pub_date = pub_date_raw
        if pub_date_raw:
            try:
                dt = parsedate_to_datetime(pub_date_raw).astimezone(HKT_TZ)
                pub_date = dt.strftime("%m/%d %H:%M")
                pub_ts = int(dt.timestamp())
            except (TypeError, ValueError, OSError):
                pub_date = pub_date_raw
                pub_ts = 0
        else:
            pub_ts = 0
        if keyword:
            data.append(
                {
                    "keyword": keyword,
                    "search_volume": traffic or "N/A",
                    "published_at": pub_date,
                    "published_ts": pub_ts,
                    "source": "rss",
                    "detail_items": detail_items,
                }
            )
    return data[:20]


def _persist_trending_keywords(data: list[dict[str, Any]]) -> None:
    TRENDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _traffic_to_int(value: str) -> int:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else 0


def _published_to_sort_ts(item: dict[str, Any]) -> int:
    raw_ts = int(item.get("published_ts") or 0)
    if raw_ts > 0:
        return raw_ts
    raw = str(item.get("published_at", "")).strip()
    if not raw:
        return 0
    try:
        dt = datetime.strptime(raw, "%m/%d %H:%M").replace(year=datetime.now(HKT_TZ).year, tzinfo=HKT_TZ)
        return int(dt.timestamp())
    except ValueError:
        return 0


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


def _render_trends_widget(trends: list[dict[str, Any]], sort_mode: str) -> None:
    items = []
    for idx, item in enumerate(trends[:12], start=1):
        details = item.get("detail_items") if isinstance(item.get("detail_items"), list) else []
        detail_items = []
        for d in details[:3]:
            detail_items.append(
                {
                    "title": str(d.get("title", "")).strip(),
                    "url": str(d.get("url", "")).strip(),
                    "source": str(d.get("source", "")).strip(),
                }
            )
        items.append(
            {
                "rank": idx,
                "keyword": str(item.get("keyword", "")).strip(),
                "volume": str(item.get("search_volume", "")).strip() or "N/A",
                "published_at": str(item.get("published_at", "")).strip() or "N/A",
                "right_text": (
                    str(item.get("published_at", "")).strip() or "N/A"
                    if sort_mode == "time"
                    else (str(item.get("search_volume", "")).strip() or "N/A")
                ),
                "detail_items": detail_items,
            }
        )

    payload = json.dumps(
        {"items": items},
        ensure_ascii=False,
    )

    html = f"""
    <div id="trends-root"></div>
    <script>
      const data = {payload};
      const root = document.getElementById('trends-root');
      const esc = (s) => String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

      root.innerHTML = `
            <style>
          :root {{
            color-scheme: light dark;
          }}
          html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
          }}
          #trends-root {{
            min-height: 100%;
            border: 1px solid rgba(196, 205, 236, 0.45);
            border-radius: 14px;
            padding: 10px;
            backdrop-filter: saturate(155%) blur(12px);
            -webkit-backdrop-filter: saturate(155%) blur(12px);
            background: rgba(238, 242, 255, 0.35);
          }}
          .tw-wrap {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          }}
          .tw-card {{
            border: 1px solid #dbe2ff;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.96);
            margin: 0 0 8px 0;
            overflow: hidden;
          }}
          .tw-card-head {{
            width: 100%;
            border: 0;
            background: transparent;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 8px;
            padding: 10px 12px;
            cursor: pointer;
          }}
          .tw-card-head:hover {{
            background: rgba(90, 90, 177, 0.06);
          }}
          .tw-left {{
            min-width: 0;
                color: #2b2b35;
            font-size: 14px;
            text-align: left;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
          }}
          .tw-right {{
                color: #5a5ab1;
                font-weight: 600;
            font-size: 13px;
            flex-shrink: 0;
          }}
          .tw-detail {{
            display: none;
            border-top: 1px solid #e8e8f8;
            padding: 8px 12px 10px;
                font-size: 12px;
            color: #3d3d4a;
            background: rgba(250, 250, 255, 0.85);
          }}
          .tw-card.expanded .tw-detail {{
            display: block;
          }}
          .tw-caption {{
            margin: 0 0 6px 0;
            color: #66667f;
            font-size: 11px;
          }}
          .tw-detail ol {{
            margin: 0 0 0 16px;
            padding: 0;
          }}
          .tw-detail li {{
            margin: 0 0 4px 0;
          }}
          .tw-detail a {{
            color: #4f56b5;
            text-decoration: underline;
          }}
          @media (prefers-color-scheme: dark) {{
            #trends-root {{
              border-color: rgba(109, 122, 163, 0.42);
              background: rgba(31, 36, 52, 0.38);
            }}
            .tw-card {{
              border-color: #4a5577;
              background: rgba(49, 58, 84, 0.88);
            }}
            .tw-left {{
              color: #eceef7;
            }}
            .tw-right {{
              color: #9ca6ff;
            }}
            .tw-card-head:hover {{
              background: rgba(156, 166, 255, 0.12);
            }}
            .tw-detail {{
              border-top-color: #3a3a4a;
              color: #d8dced;
              background: rgba(34, 37, 50, 0.95);
            }}
            .tw-caption {{
              color: #a8aec6;
            }}
          }}
        </style>
        <div class="tw-wrap">
          <div id="tw-list"></div>
        </div>
      `;

      const list = root.querySelector('#tw-list');
      const notifyFrameHeight = () => {{
        const height = Math.ceil(document.documentElement.scrollHeight);
        window.parent.postMessage(
          {{ isStreamlitMessage: true, type: "streamlit:setFrameHeight", height }},
          "*"
        );
      }};
      const renderDetails = (item) => {{
        const details = Array.isArray(item.detail_items) ? item.detail_items : [];
        const listHtml = details.length
          ? `<p class="tw-caption">趋势细分（RSS 可用字段）</p><ol>${{details.map(d => {{
              const title = esc(d.title || '');
              const url = esc(d.url || '');
              const source = esc(d.source || '');
              const link = url ? `<a href="${{url}}" target="_blank" rel="noopener noreferrer">${{title}}</a>` : title;
              return `<li>${{link}}${{source ? ` <span class="tw-caption">(${{source}})</span>` : ''}}</li>`;
            }}).join('')}}</ol>`
          : '<p class="tw-caption">趋势细分：RSS 当前未提供可用明细。</p>';
        return `
          <p class="tw-caption"><strong>${{esc(item.keyword || '')}}</strong></p>
          <p class="tw-caption">开始时间：${{esc(item.published_at || 'N/A')}}</p>
          <p class="tw-caption">搜索量：${{esc(item.volume || 'N/A')}}</p>
          ${{listHtml}}
        `;
      }};

      const cards = [];
      data.items.forEach((item) => {{
        const card = document.createElement('div');
        card.className = 'tw-card';
        card.innerHTML = `
          <button class="tw-card-head" type="button">
            <div class="tw-left">${{esc(item.rank)}}. ${{esc(item.keyword)}}</div>
            <div class="tw-right">${{esc(item.right_text)}}</div>
          </button>
          <div class="tw-detail">${{renderDetails(item)}}</div>
        `;
        const head = card.querySelector('.tw-card-head');
        head.addEventListener('click', (e) => {{
          e.stopPropagation();
          const willOpen = !card.classList.contains('expanded');
          cards.forEach(c => c.classList.remove('expanded'));
          if (willOpen) card.classList.add('expanded');
          setTimeout(notifyFrameHeight, 0);
        }});
        list.appendChild(card);
        cards.push(card);
      }});

      document.addEventListener('click', () => {{
        cards.forEach(c => c.classList.remove('expanded'));
        setTimeout(notifyFrameHeight, 0);
      }});
      window.addEventListener('resize', notifyFrameHeight);
      setTimeout(notifyFrameHeight, 0);
    </script>
    """
    components.html(html, height=560, scrolling=True)


def _render_sidebar() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background: rgba(21, 24, 36, 0.38);
            backdrop-filter: saturate(150%) blur(14px);
            -webkit-backdrop-filter: saturate(150%) blur(14px);
        }
        [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }
        @supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
            [data-testid="stSidebar"] {
                background: var(--background-color, #f6f7fc);
            }
            }
        .trends-meta-bottom {
            margin-top: 6px;
            font-size: 10px;
            color: #9aa0b3;
            line-height: 1.3;
        }
        .trends-meta-bottom a {
            color: #9aa0b3;
            text-decoration: underline;
            text-underline-offset: 2px;
        }
        .st-key-trend_refresh button {
            width: 40px;
            min-width: 40px;
            height: 40px;
            border-radius: 999px;
            padding: 0;
            font-size: 18px;
            border: 1px solid rgba(160, 170, 205, 0.45);
            background: rgba(232, 238, 255, 0.35);
        }
        .st-key-trend_sort_pop button {
            width: 40px;
            min-width: 40px;
            height: 34px;
            border-radius: 999px;
            padding: 0;
            font-size: 16px;
            }
        .trends-sort-icon {
            font-size: 15px;
            color: #9aa0b3;
            line-height: 1;
            padding-top: 7px;
        }
            </style>
            """,
            unsafe_allow_html=True,
        )
    with st.sidebar:
        st.markdown("### Google Trends（香港）")
        sort_icon_col, sort_select_col = st.columns([1, 6])
        with sort_icon_col:
            st.markdown('<div class="trends-sort-icon">⇅</div>', unsafe_allow_html=True)
        with sort_select_col:
            st.selectbox(
                "排序",
                options=["开始时间", "搜索量"],
                key="trends_sort_mode",
                label_visibility="collapsed",
            )

        sort_mode = "time" if st.session_state.get("trends_sort_mode", "开始时间") == "开始时间" else "volume"
        trends = _load_trending_keywords()
        using_rss = any(str(item.get("source", "")).lower() == "rss" for item in trends)
        refreshed_at = datetime.now(HKT_TZ).strftime("%m-%d %H:%M")

        if sort_mode == "time":
            trends = sorted(trends, key=_published_to_sort_ts, reverse=True)
        else:
            trends = sorted(
                trends,
                key=lambda x: _traffic_to_int(str(x.get("search_volume", ""))),
                reverse=True,
            )

        if trends:
            _render_trends_widget(trends=trends, sort_mode=sort_mode)
            refresh_cols = st.columns([1.5, 1, 1.5])
            with refresh_cols[1]:
                if st.button("↻", key="trend_refresh", help="重新拉取 RSS 并更新本地样本", use_container_width=True):
                    _load_trending_keywords_from_rss.clear()
                    latest = _load_trending_keywords_from_rss()
                    if latest:
                        _persist_trending_keywords(latest)
                        st.success("已刷新趋势数据。")
                    else:
                        st.warning("刷新失败，已保留现有数据。")
                    st.rerun()

            source_text = (
                f'数据源：<a href="{TRENDS_WEB_URL}" target="_blank" rel="noopener noreferrer">Google Trends RSS</a>'
                if using_rss
                else "数据源：本地样本（RSS 不可用时回退）"
            )
            st.markdown(
                f'<div class="trends-meta-bottom">{source_text}<br/>刷新时间：{refreshed_at}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("暂无热门词数据。")

        st.divider()
        if st.button("設置", use_container_width=True):
            st.session_state["settings_open"] = True

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
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(HKT_TZ)
    except ValueError:
        return None


def _card_html(item: dict[str, Any], dt_hkt: datetime) -> str:
    link = escape(str(item.get("Post URL", "#")))
    title = escape(str(item.get("title", "")))
    thumb = escape(_resolve_thumbnail_src(str(item.get("thumbnail", ""))))
    time_text = dt_hkt.strftime("%m/%d %H:%M")
    if thumb:
        thumb_html = f'<img class="post-thumb" src="{thumb}" alt="thumbnail"/>'
    else:
        thumb_html = '<div class="post-thumb-placeholder"></div>'
    return (
        f'<a class="post-card" href="{link}" target="_blank" rel="noopener noreferrer">'
        f'<div class="post-time">{time_text}</div>'
        f"{thumb_html}"
        f'<div class="post-title">{title}</div>'
        "</a>"
    )


def _collect_time_sorted_items(items: list[dict[str, Any]]) -> list[tuple[datetime, dict[str, Any]]]:
    collected: list[tuple[datetime, dict[str, Any]]] = []
    for item in items:
        dt = _parse_publish_time(str(item.get("publish_time", "")))
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
) -> str:
    subtitle_text = escape(subtitle) if subtitle else "&nbsp;"
    subtitle_html = f'<div class="board-col-subtitle">{subtitle_text}</div>'
    sticky_cls = f" board-col-sticky board-col-sticky-{sticky_slot}" if sticky_slot is not None else ""
    sticky_key_cls = f" board-col-col{sticky_slot}" if sticky_slot in (1, 2) else ""
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
        f'<div class="board-col{sticky_cls}{sticky_key_cls}">'
        f"{head_html}"
        f'<div class="post-stack">{body_html}</div>'
        "</div>"
    )


def _render_today_board() -> None:
    now_hkt = datetime.now(HKT_TZ)
    past_24h = now_hkt - timedelta(hours=24)
    next_24h = now_hkt + timedelta(hours=24)

    published_items = _collect_time_sorted_items(_load_published_items())
    scheduled_items = _collect_time_sorted_items(_load_scheduled_items())
    pending_items = _collect_time_sorted_items(_load_pending_base())

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
    active_categories = set(selected_categories or [])

    published_cards = [
        _card_html(item, dt)
        for dt, item in sorted(published_items, key=lambda x: x[0], reverse=True)
        if past_24h <= dt <= now_hkt and (not active_categories or str(item.get("category", "未分類")) in active_categories)
    ]
    scheduled_cards = [
        _card_html(item, dt)
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
        category_cards = [_card_html(item, dt) for dt, item in pending_by_category.get(category, [])]
        board_html += _build_column_html(category, category_cards, subtitle="已出未排")
    board_html += "</div></div></div></div>"
    st.markdown(board_html, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="主頁FB排程", page_icon="🗂️", layout="wide")
    st.title("主頁FB排程")
    st.caption("Demo 版：单页总览（已發佈 / 已排程 / 已出未排），仅保留 Telegram 基础设置与测试消息。")

    _init_settings_state()
    _render_sidebar()
    _render_settings_dialog_if_needed()
    _render_today_board()


if __name__ == "__main__":
    main()

