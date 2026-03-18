from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.bot.review_bot import TelegramAPIError, get_bot_profile, send_text_message
from src.dashboard.config import (
    CHAT_ID_ENV,
    DEFAULT_SCHEDULE_WINDOW_MINUTES,
    HKT_TZ,
    SCHEDULE_WINDOW_OPTIONS,
    TOKEN_ENV,
    TRENDS_WEB_URL,
)
from src.dashboard.data_utils import (
    load_trending_keywords,
    load_trending_keywords_from_rss,
    persist_trending_keywords,
    published_to_sort_ts,
    traffic_to_int,
)


def init_settings_state() -> None:
    st.session_state.setdefault("cfg_token", os.getenv(TOKEN_ENV, ""))
    st.session_state.setdefault("cfg_chat_id", os.getenv(CHAT_ID_ENV, ""))
    st.session_state.setdefault("settings_open", False)
    st.session_state.setdefault("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)
    st.session_state.setdefault("cfg_schedule_window_minutes", st.session_state.get("schedule_window_minutes"))


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

    st.divider()
    st.caption("排程设置")
    st.selectbox(
        "排程窗口（分钟）",
        options=SCHEDULE_WINDOW_OPTIONS,
        key="cfg_schedule_window_minutes",
        help="仅确认后生效。生效后会刷新看板分钟粒度。",
    )
    if st.button("确认排程窗口", use_container_width=True):
        chosen = int(st.session_state.get("cfg_schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES))
        st.session_state["schedule_window_minutes"] = chosen
        st.session_state["settings_open"] = False
        st.session_state["board_flash"] = f"排程窗口已更新为 {chosen} 分钟。"
        st.rerun()


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

    payload = json.dumps({"items": items}, ensure_ascii=False)

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


def render_sidebar() -> None:
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
        trends = load_trending_keywords()
        using_rss = any(str(item.get("source", "")).lower() == "rss" for item in trends)
        refreshed_at = datetime.now(HKT_TZ).strftime("%m-%d %H:%M")

        if sort_mode == "time":
            trends = sorted(trends, key=published_to_sort_ts, reverse=True)
        else:
            trends = sorted(
                trends,
                key=lambda x: traffic_to_int(str(x.get("search_volume", ""))),
                reverse=True,
            )

        if trends:
            _render_trends_widget(trends=trends, sort_mode=sort_mode)
            refresh_cols = st.columns([1.5, 1, 1.5])
            with refresh_cols[1]:
                if st.button("↻", key="trend_refresh", help="重新拉取 RSS 并更新本地样本", use_container_width=True):
                    load_trending_keywords_from_rss.clear()
                    latest = load_trending_keywords_from_rss()
                    if latest:
                        persist_trending_keywords(latest)
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
            st.session_state["cfg_schedule_window_minutes"] = int(
                st.session_state.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)
            )
            st.session_state["schedule_dialog_open"] = False
            st.session_state["schedule_pick_item_id"] = ""
            st.session_state["settings_open"] = True

        if not hasattr(st, "dialog"):
            with st.expander("設置", expanded=st.session_state.get("settings_open", False)):
                _render_settings_content()


def render_settings_dialog_if_needed() -> None:
    if not hasattr(st, "dialog"):
        return
    if st.session_state.get("schedule_dialog_open", False):
        return

    @st.dialog("設置")
    def _settings_dialog() -> None:
        _render_settings_content()
        if st.button("關閉", use_container_width=True):
            st.session_state["settings_open"] = False
            st.rerun()

    if st.session_state.get("settings_open", False):
        _settings_dialog()
