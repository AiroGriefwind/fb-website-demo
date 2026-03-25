from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure imports like `from src...` work when launched via `streamlit run src/dashboard/app.py`.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.dashboard.board_view import render_today_board
from src.dashboard.live_api_sync import sync_live_data_to_sample_files
from src.dashboard.sidebar_view import (
    init_settings_state,
    render_settings_dialog_if_needed,
    render_sidebar,
)


def get_dashboard_health() -> dict[str, str]:
    return {"status": "ok", "module": "dashboard"}


def main() -> None:
    st.set_page_config(page_title="主頁FB排程", page_icon="🗂️", layout="wide")
    st.title("主頁FB排程")
    st.caption("Demo 版：单页总览（已發佈 / 已排程 / 已出未排），仅保留 Telegram 基础设置与测试消息。")

    init_settings_state()

    has_ui_only_query = any(
        x in st.query_params
        for x in ("schedule_pick", "update_pick", "delete_pick", "unschedule_pick", "lock_toggle")
    )
    has_pending_action = bool(st.session_state.get("pending_fb_action"))
    if has_ui_only_query and not has_pending_action:
        st.caption("正在打开操作弹窗，暂不触发 API 同步。")
    else:
        sync_result = sync_live_data_to_sample_files(
            enable_category_alias_mode=bool(st.session_state.get("cfg_enable_category_alias_mode", False)),
            target_fan_page_id=str(st.session_state.get("cfg_target_fan_page_id", "350584865140118")).strip(),
        )
        if sync_result.get("ok"):
            st.caption(
                "已从 API 同步："
                f"已發佈 {int(sync_result.get('published_count', 0))} ｜ "
                f"已排程 {int(sync_result.get('scheduled_count', 0))} ｜ "
                f"已出未排 {int(sync_result.get('pending_count', 0))}"
            )
        else:
            st.warning(
                "API 同步失败，已回退现有样本数据。"
                f" 原因：{sync_result.get('message', 'unknown')}"
            )
        with st.expander("API 同步调试详情（临时）", expanded=True):
            st.caption("以下为本次同步请求与响应原文（用于排查 401/鉴权/网关问题）。")
            st.json(sync_result)

    render_sidebar()
    render_today_board()
    render_settings_dialog_if_needed()


if __name__ == "__main__":
    main()
