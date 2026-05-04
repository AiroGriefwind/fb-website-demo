from __future__ import annotations

"""Dashboard API 入口（uvicorn）。

看板左下「设置」中的 CMS 上游开关（Staging / Production）由 FastAPI 写入
`data/samples/dashboard_settings_state.json`，服务端 `CmsActionClient` 与 Live 同步均遵循：
Production 时为网关 Basic + JSON 登录 + 后续请求 ``Authorization: Basic`` + ``X-Token`` + ``Cookies``（与 ``api_smoke_test_app`` 成功组合一致）。
"""

import uvicorn


def main() -> None:
    uvicorn.run("src.dashboard_api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

