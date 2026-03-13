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
  - `st.session_state`：配置项、弹窗开关、筛选状态、拖放回传状态。
  - `st.dialog`：设置弹窗与排程时间弹窗（分钟粒度 5 分钟）。
  - `st.query_params`：拖放动作的前后端桥接参数（`schedule_pick`）。
- 数据加载与回退：
  - 本地 JSON 样本读写：`_read_json_list()`、`_write_json_list()`。
  - API 可选加载 + 本地回退：`_load_from_api()`、`_load_dataset()`。
  - 拖拽排程写回：`_move_pending_item_to_scheduled()`（pending -> scheduled）。
- 看板渲染与交互：
  - 九列看板渲染：`_render_today_board()` + `_build_column_html()` + `_card_html()`。
  - 前两列 sticky 与收起控制（左侧控制栏 + 列头联动）。
  - 拖拽排程（桌面拖拽 + 移动端长按兜底）：通过 `streamlit.components.v1.html` 注入前端脚本实现 drop 监听。
- 趋势与侧边栏：
  - Google Trends RSS：`urllib.request` + `xml.etree.ElementTree` 解析，`@st.cache_data(ttl=900)` 缓存。
  - 侧边栏趋势卡片使用 `components.html` 自定义交互（展开/排序/刷新）。
- 媒体与样式：
  - 本地缩略图通过 base64 data URI 渲染：`_file_to_data_uri()`、`_resolve_thumbnail_src()`。
  - 分类浅色配色体系：`_category_style_tokens()` + `CATEGORY_INTENSITY_OVERRIDES`。
  - 大量定制 CSS（sticky 遮罩、横向滚动、响应式断点、卡片视觉反馈）。

## 目录级约束
- 所有可执行入口必须在 `src/` 或 `scripts/`。
- 运行产物（截图、临时 JSON、HTML dump）必须落在 `artifacts/`。
- 长期样例数据放在 `data/`，且仅保留脱敏样本。

