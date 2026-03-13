# STARTUP

## 通用开场提示（给每个 worktree 的 LLM）
```text
你现在在 BP-CMS-Scraper 的功能分支中开发。
开始任何实现前，必须完整阅读以下文件并在回复中确认已读：
1) docs/governance/PRD.MD
2) docs/governance/TECHSTACK.MD
3) docs/governance/STRUCTURE.MD
4) docs/governance/IMPLEMENTATION_PLAN.MD
5) docs/governance/PROGRESS.MD
6) docs/governance/STARTUP.MD

要求：
- 仅在当前功能分支职责范围内改动代码。
- 每完成一步必须补写 docs/governance/PROGRESS.MD。
- 优先小步提交，提交信息带分支前缀。
- 不得改动其他功能分支核心目录。
```

## 分支专项提示

### feature/scraper-core
```text
目标：稳定抓取 CMS -> FB 数据，完善错误恢复与结构化输出。
重点目录：src/scraper、src/common
验收：48h 抓取稳定，失败可追踪，字段完整。
```

### feature/scoring-pipeline
```text
目标：实现规则+LLM 评分融合、排序与候选池。
重点目录：src/scoring
验收：给定样本可复现评分结果，并有解释字段。
```

### feature/scheduler-dispatch
```text
目标：根据评分结果生成排程，规避冲突与时段限制。
重点目录：src/scheduler
验收：同一时间槽无冲突，输出可审计的排程计划。
```

### feature/bot-ui-ops
```text
目标：Telegram 审核流 + Streamlit 控制台。
重点目录：src/bot、src/dashboard
验收：可完成待审->通过/否决->状态回写全流程。
Demo 阶段补充：
- 外部 demo 仓库可作为短期主要 push 目的地（用于客户演示与快速迭代）。
- 本仓库仍保留治理与主线进度职责；每次 demo 迭代必须回写 docs/governance/PROGRESS.MD 做映射记录。
- 未明确回迁前，不得将 demo 仓库改动表述为“本仓库已落地”。
```

#### 开场白提示词：Json -> PostgreSQL（并发与审计）
```text
你当前负责将 dashboard 的本地 JSON 状态管理迁移到 PostgreSQL（面向公司内部 <=10 人并发）。
必须先完整阅读 docs/governance/PRD.MD、TECHSTACK.MD、STRUCTURE.MD、IMPLEMENTATION_PLAN.MD、PROGRESS.MD、STARTUP.MD，并在回复中确认已读。
目标：
- 将 pending/scheduled 读写从文件迁移到数据库事务，避免并发覆盖。
- 保留可审计事件日志（谁在何时做了什么）。
- 兼容现有 UI 交互（拖拽排程、时间弹窗、状态刷新）。
约束：
- 仅改动 src/dashboard（必要时补充最小 scripts/configs），不改其他分支核心目录。
- 每完成一步必须回写 docs/governance/PROGRESS.MD。
- 未完成回迁前，不将 demo 仓库验证结果表述为“本仓库已落地”。
```

#### 开场白提示词：登录与访问控制
```text
你当前负责为 dashboard 增加登录与访问控制能力（内部账号体系，未登录不可访问）。
必须先完整阅读 docs/governance/PRD.MD、TECHSTACK.MD、STRUCTURE.MD、IMPLEMENTATION_PLAN.MD、PROGRESS.MD、STARTUP.MD，并在回复中确认已读。
目标：
- 实现最小可用的登录链路（登录/退出/会话校验）。
- 在未授权场景阻断 dashboard 页面访问。
- 预留后续接入 Cloudflare Access / OIDC / 企业 SSO 的扩展点。
约束：
- 仅改动 src/dashboard、src/common（如需）；不引入明文密钥到仓库。
- 所有凭据通过环境变量或 secret 管理，不写死在代码中。
- 每完成一步必须回写 docs/governance/PROGRESS.MD。
```

#### 开场白提示词：假数据 -> API 真数据
```text
你当前负责将 dashboard 从样本 JSON 驱动迁移为 API 真数据驱动，同时保留本地 fallback。
必须先完整阅读 docs/governance/PRD.MD、TECHSTACK.MD、STRUCTURE.MD、IMPLEMENTATION_PLAN.MD、PROGRESS.MD、STARTUP.MD，并在回复中确认已读。
目标：
- 固化 published/scheduled/pending/trends 的 API 字段契约与错误处理策略。
- 将加载链路统一到 API 优先、失败回退样本的可观测流程。
- 确保拖拽排程与状态写回可对接后端 API（而非仅本地文件）。
约束：
- 仅在 feature/bot-ui-ops 范围改动（src/dashboard、必要的接口适配层）。
- 明确区分“本仓库已落地”与“demo 仓库已验证”。
- 每完成一步必须回写 docs/governance/PROGRESS.MD。
```

### feature/infra-observability
```text
目标：cron、日志归档、告警、升级脚本。
重点目录：scripts、configs、docs/runbooks
验收：定时任务可跑通，日志可查，升级可回滚。
```

