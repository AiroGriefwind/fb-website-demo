from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure imports like `from src...` work when launched via `streamlit run src/dashboard/app.py`.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.dashboard.board_view import render_today_board
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
    render_sidebar()
    render_today_board()
    render_settings_dialog_if_needed()


if __name__ == "__main__":
    main()
