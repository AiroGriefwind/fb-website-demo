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
```

### feature/infra-observability
```text
目标：cron、日志归档、告警、升级脚本。
重点目录：scripts、configs、docs/runbooks
验收：定时任务可跑通，日志可查，升级可回滚。
```

