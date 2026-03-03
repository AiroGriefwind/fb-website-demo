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

## 目录级约束
- 所有可执行入口必须在 `src/` 或 `scripts/`。
- 运行产物（截图、临时 JSON、HTML dump）必须落在 `artifacts/`。
- 长期样例数据放在 `data/`，且仅保留脱敏样本。

