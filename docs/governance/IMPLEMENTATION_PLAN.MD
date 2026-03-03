# IMPLEMENTATION_PLAN

## 执行守则（降低幻觉率）
- 任何 LLM/开发者在开始编码前，必须完整阅读：
  - `docs/governance/PRD.MD`
  - `docs/governance/TECHSTACK.MD`
  - `docs/governance/STRUCTURE.MD`
  - `docs/governance/PROGRESS.MD`
  - `docs/governance/STARTUP.MD`
  - 本文件 `docs/governance/IMPLEMENTATION_PLAN.MD`
- 未阅读上述文件，不得开始实现或改动代码。
- 每完成一个可验证步骤，必须回写 `docs/governance/PROGRESS.MD`。

## Phase A：基础治理与结构
1. 建立文档群与模板约束。
2. 根目录重构：将源码、配置、数据、产物归位。
3. 保持兼容入口，避免一次性破坏既有脚本调用。

## Phase B：抓取与数据标准化
1. 拆分抓取逻辑为模块化结构（登录、导航、抓取、解析、持久化）。
2. 定义统一输出模型：`post_id/title/datetime/reached/engaged/category/run_id`。
3. 增加容错：重试、超时、页面异常兜底与截图留证。

## Phase C：评分与候选池
1. 规则评分（时效、标签、位置、历史表现）。
2. LLM 评分（热点讨论度、风险标签、可发布性）。
3. 融合排序并生成候选池，记录评分解释字段。

## Phase D：排程与发布准备
1. 时段策略与冲突规避。
2. photo/text 的发布约束。
3. 人工审核前置队列构建。

## Phase E：人工介入与运维
1. Telegram 审核流（通过/否决/微调/超时自动确认）。
2. Streamlit 中控台（任务、日志、告警）。
3. Firebase Storage 日志归档。
4. GCP VM 升级脚本与服务重启流程。

## Phase F：上线与回归
1. cronjob 定时编排（抓取、评分、发送、归档）。
2. 告警链路压测与演练。
3. 失败恢复演练（网络异常、登录失败、解析失败）。

