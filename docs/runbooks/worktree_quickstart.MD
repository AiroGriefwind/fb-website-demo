# Worktree Quickstart

## 目标
- 支持你同时打开多个 Cursor 窗口并行推进，减少跨功能冲突。

## 分支与目录映射
- `feature/scraper-core` -> `D:/workFiles/BP-CMS-Scraper-scraper-core`
- `feature/scoring-pipeline` -> `D:/workFiles/BP-CMS-Scraper-scoring-pipeline`
- `feature/scheduler-dispatch` -> `D:/workFiles/BP-CMS-Scraper-scheduler-dispatch`
- `feature/bot-ui-ops` -> `D:/workFiles/BP-CMS-Scraper-bot-ui-ops`
- `feature/infra-observability` -> `D:/workFiles/BP-CMS-Scraper-infra-observability`

## 每个窗口启动后第一步
1. 打开对应 worktree 目录。
2. 先阅读 `docs/governance/` 下全部文档。
3. 只改本分支负责目录，不跨模块大改。
4. 完成一步就更新 `docs/governance/PROGRESS.MD`。

## 合并顺序建议
1. `feature/scraper-core`
2. `feature/scoring-pipeline`
3. `feature/scheduler-dispatch`
4. `feature/bot-ui-ops`
5. `feature/infra-observability`

