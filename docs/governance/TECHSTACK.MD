# TECHSTACK

## 运行环境
- Python 3.10+
- GCP Compute Engine VM（`e2-micro`）
- Linux cronjob（UTC 存储，业务按 HKT 转换）

## 核心模块技术选型
- 抓取自动化：Selenium + Chrome/Chromedriver
- 任务编排：cron + Python CLI 任务入口
- 人工介入：
  - Telegram Bot（审核交互、告警确认）
  - Streamlit（中控台、日志浏览、手动触发）
- 存储与日志：
  - Firebase Storage（原始日志、产物归档）
  - Firebase Realtime Database/Firestore（任务状态索引，可选）
- 质量与可观测：
  - 结构化日志（JSON line）
  - 心跳检测 + 错误告警
- 升级与运维：
  - Shell Script（拉取代码、安装依赖、重启服务）
  - systemd/supervisor（二选一，建议 systemd）

## 第三方能力（计划）
- LLM 评分（可切换供应商）
- Gmail 告警（OAuth，指定发件账号）

## Streamlit 当前实现（feature/bot-ui-ops）
- 页面与状态管理：
  - `st.session_state`：配置项、弹窗开关、筛选状态、排程目标状态。
  - `st.dialog`：设置弹窗与排程时间弹窗（分钟粒度 5 分钟）。
  - `st.query_params`：排程触发参数（`schedule_pick`）。
- 数据加载与回退：
  - 本地 JSON 样本读写：`_read_json_list()`、`_write_json_list()`。
  - API 可选加载 + 本地回退：`_load_from_api()`、`_load_dataset()`。
  - 排程写回：`_move_pending_item_to_scheduled()`（pending -> scheduled）。
- 看板渲染与交互：
  - 九列看板渲染：`_render_today_board()` + `_build_column_html()` + `_card_html()`。
  - 前两列 sticky 与收起控制（左侧控制栏 + 列头联动）。
  - 第 3~9 列排程触发：点击卡片顶部 `📅` 按钮写入 `schedule_pick` 并拉起排程弹窗。
- 趋势与侧边栏：
  - Google Trends RSS：`urllib.request` + `xml.etree.ElementTree` 解析，`@st.cache_data(ttl=900)` 缓存。
  - 侧边栏趋势卡片使用 `components.html` 自定义交互（展开/排序/刷新）。
- 媒体与样式：
  - 本地缩略图通过 base64 data URI 渲染：`_file_to_data_uri()`、`_resolve_thumbnail_src()`。
  - 分类浅色配色体系：`_category_style_tokens()` + `CATEGORY_INTENSITY_OVERRIDES`。
  - 大量定制 CSS（sticky 遮罩、横向滚动、响应式断点、卡片视觉反馈）。

## FastAPI 看板 UI（当前主用）
- 前端：
  - 原生 `HTML + CSS + JavaScript` 单页界面，入口为 `frontend/board/index.html`。
  - 交互状态管理使用 `Alpine.js`（CDN 引入，无 React/Vue 构建链）。
  - 通过 `fetch("/api/...")` 调用 FastAPI 接口，局部刷新已发布 / 已排程 / 已出未排列。
- 后端：
  - `FastAPI` 提供 `/api/board/columns`、`/api/actions/publish|update|delete|toggle-lock`、侧栏设置与趋势接口。
  - 使用 `StaticFiles` 挂载 `/board`（前端静态页面）与 `/assets`（样本图片/资源）。
  - 运行入口为 `src/dashboard_api/run.py`，由 `uvicorn` 启动 `src.dashboard_api.server:app`。
- 数据来源与刷新：
  - 看板 UI 主要读取 `data/samples/*.json` 样本文件。
  - Live 模式下由 `src/dashboard.live_api_sync` 拉取 CMS `fb_published` / `fb_scheduled` / `posts` 并重写样本文件。
  - 手动「刷新全部」与部分动作后的 UI 回读都经由 FastAPI 完成；局部刷新应尽量复用已同步好的样本，避免重复全量拉取上游。

## 目录级约束
- 所有可执行入口必须在 `src/` 或 `scripts/`。
- 运行产物（截图、临时 JSON、HTML dump）必须落在 `artifacts/`。
- 长期样例数据放在 `data/`，且仅保留脱敏样本。

