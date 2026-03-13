# PROGRESS

## 使用规则
- 每次推进后追加一条，不覆盖历史。
- 记录必须包含：时间、分支/worktree、完成项、验证、风险、下一步。

## 跨仓库记录约定（Demo 阶段）
- 本仓库仍是 `BP-CMS-Scraper` 项目治理与主线追踪的记录面板；外部 demo 仓库用于短期演示迭代与高频发布。
- Demo 阶段若主要改动发生在外部仓库，也必须在本文件追加记录，明确“改动发生地”和“影响范围”。
- `分支/worktree` 字段统一写法：`本仓库分支 | demo仓库:<repo>/<branch>@<commit或tag>`。
- `完成内容` 至少包含两类标记之一：`[本仓库]`、`[demo仓库]`，避免后续误判代码已在本仓库落地。
- 未回迁前，禁止在本文件将 demo 仓库改动描述为“本仓库已实现”；只能写“已在 demo 仓库验证”。
- 回迁发生时，必须单独追加一条“回迁记录”，写清来源 commit/tag、回迁范围、差异处理与验证结论。

## 记录模板
```text
日期时间(HKT):
负责人/LLM:
分支/worktree:
完成内容:
- 

验证结果:
- 

风险/阻塞:
- 

下一步:
- 
```

## Changelog

日期时间(HKT): 2026-03-03
负责人/LLM: gpt-5.3-codex
分支/worktree: main
完成内容:
- 完成仓库体检与重构计划落地。
- 新建治理文档：PRD/TECHSTACK/IMPLEMENTATION_PLAN/PROGRESS/STARTUP/STRUCTURE。

验证结果:
- 文档已创建并可读。

风险/阻塞:
- 当前仓库存在历史未整理产物，重构后需保持工作流兼容性。

下一步:
- 执行目录迁移与兼容入口整理。



鏃ユ湡鏃堕棿(HKT): 2026-03-03
璐熻矗浜?LLM: gpt-5.3-codex
鍒嗘敮/worktree: main
瀹屾垚鍐呭:
- 绉婚櫎 GitHub Actions workflow 涓?Dockerfile銆俓n- 灏嗘不鐞嗙被 Markdown 杩佺Щ鑷?docs/governance 涓撳尯銆俓n- 瀹屾垚鍩虹鐩綍閲嶆瀯涓庡吋瀹瑰叆鍙ｄ繚鐣欍€俓n- 鏂板妯″潡楠ㄦ灦涓庡绾︼細浠诲姟鐘舵€併€佸鏍镐簨浠躲€佹棩蹇楄褰曠粨鏋勩€俓n
楠岃瘉缁撴灉:
- 鐩綍缁撴瀯涓庢枃妗ｈ矾寰勪竴鑷淬€俓n- Python 鏂囦欢鏃犳柊澧?lint 闂銆俓n
椋庨櫓/闃诲:
- 鍚庣画鎷嗗垎鍒板悇鍔熻兘鍒嗘敮鏃讹紝闇€閬垮厤鍦ㄩ潪璐熻矗鐩綍鍋氬ぇ鏀广€俓n
涓嬩竴姝?
- 灏嗗綋鍓嶅熀绾挎彁浜ゅ埌 main 骞舵帹閫併€俓n- 鍚屾 cherry-pick 鍒板悇 feature 鍒嗘敮骞舵帹閫佽繙绔€俓n

日期时间(HKT): 2026-03-04
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 将 `src/bot/review_bot.py` 从占位实现升级为 Telegram API 工具层，支持 token 校验（getMe）、文本消息发送、待审消息格式化与发送。
- 将 `src/dashboard/app.py` 实现为可运行 Streamlit 控制台，支持：Bot Token/Chat ID 配置、连通测试、发送待审消息、待审项通过/否决与状态回写。
- 新增运行时持久化：`data/runtime/review_queue.json`（队列快照）与 `data/runtime/review_events.jsonl`（审核事件日志，运行时生成）。

验证结果:
- 代码级检查通过：模块导入关系正确，核心异常路径（无 token、API 返回非 ok、网络异常）均有 UI 提示。
- 运行方式已明确：`streamlit run src/dashboard/app.py`，可在页面直接验证 Telegram 连通与消息发送。

风险/阻塞:
- 目前回写目标为本地 `data/runtime`，尚未接入 Firebase 索引层。
- 审核动作通过控制台按钮触发，尚未启用 Telegram inline 按钮回调。

下一步:
- 对接真实待审队列来源（scheduler 输出）并统一 `run_id/item_id` 生命周期。
- 增加 Telegram 侧交互回调（通过/否决）并回写同一状态存储。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 修复 `streamlit run src/dashboard/app.py` 启动时 `ModuleNotFoundError: No module named 'src.bot'` 问题。
- 在 `src/dashboard/app.py` 增加启动时 `sys.path` 引导，将项目根目录注入模块搜索路径，保证 `from src...` 导入稳定可用。

验证结果:
- 本地语法编译通过，导入路径修复后可进入 Streamlit 页面加载流程（不再在导入阶段报错）。

风险/阻塞:
- 若使用非常规启动方式（例如外部 runner 修改工作目录），仍建议从仓库根目录执行 Streamlit 命令。

下一步:
- 用户侧重启 Streamlit 并完成 token/chat_id 实测。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 里程碑1：重构 `src/dashboard/app.py` 顶层布局，页面标题改为“主頁FB排程”，主内容切换为 `已發佈/已排程/待排程` 三 Tab 架构。
- 侧边栏重构为趋势词区 + 设置入口区，保留后续扩展空间。

验证结果:
- 代码结构检查通过：旧单页审核逻辑已迁移为 Tab 结构，核心入口 `main()` 可正常解析。

风险/阻塞:
- 当前趋势词与业务列表仍依赖本地数据文件，需在后续里程碑补充 mock 数据并接入加载层。

下一步:
- 完成里程碑2：补齐三类业务数据与 Google Trends 的 mock JSON 文件。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 里程碑2：新增并填充 4 份 demo 数据文件：`dashboard_published.json`、`dashboard_scheduled.json`、`dashboard_pending.json`、`google_trends_hk_mock.json`。
- 数据字段与约定 API 结构对齐：`title/thumbnail/Post URL/publish_time/popular_count`，待排程额外包含 `item_id/category/review_status`。

验证结果:
- JSON 结构为标准数组对象格式，可被控制台加载函数直接读取。

风险/阻塞:
- 当前趋势词为静态 mock，不含实时更新机制。

下一步:
- 完成里程碑3：实现 `設置` 弹层并迁移 Telegram 配置与联通测试操作。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 里程碑3：在侧边栏新增 `設置` 按钮，接入设置弹层能力；优先使用 `st.dialog`，并在不支持时回退到 `st.expander`。
- 将 Bot Token / Chat ID、`验证 token`、`发送测试消息` 统一迁移到设置面板中。

验证结果:
- 设置入口逻辑可用：点击 `設置` 后可进入配置面板并执行 Telegram 联通测试。

风险/阻塞:
- 由于 Streamlit 版本差异，弹层表现可能在不同环境存在细微差异，已提供降级方案确保可用性。

下一步:
- 完成里程碑4：实现三 Tab 数据渲染与待排程七栏目分组审核交互。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 里程碑4：完成 `已發佈`、`已排程`、`待排程` 三个 Tab 的独立渲染逻辑。
- `待排程` 按 `娛樂/社會事/大視野/兩岸/法庭事/消費/心韓` 七个栏目分组为 expander，并在组内提供通过/否决/发送 Telegram 操作。
- 新增待排程状态统计（待排程/已通过/已否决）及运行时状态持久化文件 `data/runtime/dashboard_pending_runtime.json`。

验证结果:
- 审核动作可更新状态并写入 `data/runtime/review_events.jsonl`，再次进入页面时可保持待排程列表状态。

风险/阻塞:
- 当前 UI 未加入分页，栏目数据量较大时需要后续补充筛选与检索能力。

下一步:
- 完成里程碑5：抽象 `load_*` 数据加载层并预留 API Base URL 环境变量。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 里程碑5：在 `src/dashboard/app.py` 完成数据加载抽象（`_load_dataset` + `load_*` 组合），默认读本地 JSON，同时预留 API 加载路径。
- 新增 `DASHBOARD_API_BASE_URL` 环境变量入口；当配置后按 `published/scheduled/pending/trends` 路径拉取数据，失败时回退本地样本。

验证结果:
- 代码路径检查通过：无 API 配置时使用样本数据；具备 API 时可切换为 HTTP 数据源。

风险/阻塞:
- API 返回结构需与 mock 字段保持一致，否则 UI 渲染会出现字段缺失。

下一步:
- 与后端对齐 API 返回字段，并补充 Nginx 反向代理与访问控制配置文档。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 根据最新 UI 要求，将 `已發佈` 与 `已排程` 两个 Tab 改为周历视图：横向 7 天、纵向 00:00 到 23:59。
- 增加周范围导航：`往前七天` / `往后七天`，并显示当前周日期区间。
- 每条贴文渲染为可点击卡片（左上角时间、预览图、标题两行省略），点击后跳转 JSON 中 `Post URL`。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 当前按小时分组显示；若同一小时贴文过多，会在单元格内堆叠，需要后续加筛选或密度优化。

下一步:
- 依据真实 API 数据量优化周历性能与单元格可读性（如懒加载、按栏目过滤）。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 接入 `data/samples/Dummy1.png` 作为 demo 统一缩略图来源，保留在 `data/samples` 目录（符合样本数据落位规范）。
- `src/dashboard/app.py` 增加本地图片路径解析与 data URI 转换逻辑，确保周历卡片可直接渲染本地样本图。
- 将 `dashboard_published.json`、`dashboard_scheduled.json`、`dashboard_pending.json` 的 `thumbnail` 字段统一改为 `data/samples/Dummy1.png`。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- data URI 会增加页面 HTML 体积；当前 demo 数据量较小影响可接受，后续接真实数据建议改为可访问静态 URL。

下一步:
- 若后续图片数量增大，补充静态资源服务层（或 API 返回 CDN URL）以降低前端渲染负担。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 按最新反馈优化周视图 UI：移除小时网格表格样式，不再显示类似 Excel 的横纵线结构。
- `已發佈` / `已排程` 改为“每天一列、卡片纵向等间距堆叠”，并保持贴文按发布时间升序排列（最早在上方）。
- 保留周切换导航（往前/往后七天）与点击卡片跳转 URL 的交互。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 单日贴文过多时纵向长度会显著增加，后续可加折叠或“仅显示前 N 条”策略。

下一步:
- 根据真实数据密度决定是否加入“按栏目/关键词过滤”与“单日展开收起”交互。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 优化贴文卡片可点击反馈：新增 hover 过渡效果（边框高亮、阴影、轻微上浮、透明度变化），提升可点击感知。
- 优化侧边栏 Google Trends 列表：每行增加卡片托底样式，关键词左对齐、搜索量右对齐显示，视觉更清晰。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 当前趋势行样式在极窄侧栏宽度下会发生文本截断，已启用省略号处理。

下一步:
- 创建新的 GitHub public demo 仓库并推送当前版本，供同事线上预览。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 优化周视图在移动端的展示策略：不再压缩卡片比例，改为横向可滚动容器承载 7 天列。
- 宽屏继续完整展示 7 天；窄屏时保持卡片宽度下限并启用左右滑动查看不同日期列。
- 增加滚动条样式与提示文案（小屏设备可左右滑动查看整周）。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 不同手机浏览器对滚动条可见性策略不同，个别机型可能仅显示手势滑动、不显示明显滚动条。

下一步:
- 根据同事手机实测反馈微调日列最小宽度与卡片密度。

日期时间(HKT): 2026-03-09
负责人/LLM: gpt-5.3-codex
分支/worktree: feature/bot-ui-ops
完成内容:
- 扩充 `data/samples/dashboard_published.json` 与 `data/samples/dashboard_scheduled.json`：新增 `category` 字段，并按 3月9日/3月10日、每类每天3篇生成样本（每个文件 42 篇）。
- 在 `已發佈` 与 `已排程` 周视图中新增 `分類篩選` 多选框，位置在日期区间 UI 下方，可按一个或多个分类过滤贴文。
- 分类选项与 `待排程` 维持一致（娛樂/社會事/大視野/兩岸/法庭事/消費/心韓），并保留未分类兜底。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。
- 样本数据文件检查通过：两份数据均包含 `category` 且数量满足要求。

风险/阻塞:
- 当前分类筛选默认全选；若用户手动清空所有选项，页面会回退展示全部分类（可按后续反馈调整为“显示空结果”）。

下一步:
- 将本次更新推送到 `fb-website-demo` 仓库，供线上继续验收。

日期时间(HKT): 2026-03-11
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: main（本仓库治理） | demo仓库: AiroGriefwind/fb-website-demo/main@877aec634ecf4bf8998a5131dc9d2a341aebaff2
完成内容:
- [治理] 明确 Demo 阶段策略：短期以外部 demo 仓库作为主要 push 目的地，本仓库持续承担 BP-CMS-Scraper 主线治理与进度归档。
- [治理] 新增跨仓库记录约定，要求后续每次演示迭代都在本文件追加映射记录，避免未来合并时混淆“已演示”与“已回迁”。
- [计划] 回迁动作延期到 demo 阶段结束后（客户验收、仓库转 private、交付部署包）再评估执行。

验证结果:
- 文档规则已落地：后续可通过统一 `分支/worktree` 模式和 `[本仓库]/[demo仓库]` 标记追溯改动归属。

风险/阻塞:
- 若 demo 仓库未持续填写 commit/tag 映射，本仓库将丢失可审计的版本对应关系。
- demo 仓库与本仓库长期并行可能导致实现漂移，需在回迁前安排一次差异盘点。

下一步:
- 从下一次 demo 提交开始，在本文件记录 demo 仓库 `repo/branch/commit(tag)` 映射。
- demo 阶段结束后追加“回迁决策记录”（回迁/不回迁/部分回迁）并给出执行窗口。

日期时间(HKT): 2026-03-11
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（治理记录） | demo仓库: AiroGriefwind/fb-website-demo/main@877aec634ecf4bf8998a5131dc9d2a341aebaff2
完成内容:
- [demo仓库] 补齐 demo 仓库地址与建仓后关键提交映射：`https://github.com/AiroGriefwind/fb-website-demo`。
- [demo仓库] `1462afc`：`feature/bot-ui-ops: streamlit demo UI polish and sample data`。
- [demo仓库] `d3d900c`：`chore: remove cms_scraper.py from public demo repo`。
- [demo仓库] `877aec634ecf4bf8998a5131dc9d2a341aebaff2`：`feature/bot-ui-ops: add category filter and expand published/scheduled samples`。

验证结果:
- 本仓库治理文档中的 demo 映射信息已可直接定位到仓库、分支与关键 commit，便于后续回迁/审计。

风险/阻塞:
- 若后续只记录短 hash 且提交增多，可能出现前缀冲突；需至少保证唯一前缀长度（建议 10-12 位）。

下一步:
- 后续每次 demo push 后追加一条映射记录（建议包含 `repo/branch/commit` 与 1 行变更摘要）。
- demo 阶段结束时新增“回迁决策记录”并标注是否对齐到本仓库对应 commit。

日期时间(HKT): 2026-03-11
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@877aec634ecf4bf8998a5131dc9d2a341aebaff2
完成内容:
- [本仓库] `src/dashboard/app.py` 改为单页九列视图，移除 `已發佈/已排程/待排程` Tab 与“往前七天/往后七天”周导航。
- [本仓库] 删除待排程审核流相关函数与侧边栏“重置待排程（樣本）”按钮，仅保留 Telegram 设置、token 验证与测试消息发送。
- [本仓库] 新增横向滚动九列布局并冻结前两列（已發佈/已排程）；第3~9列固定为 `社會事/大視野/兩岸/法庭事/消費/娛樂/心韓`，列头增加小字“已出未排”。
- [本仓库] 按 HKT 实现时间窗口与排序：已發佈=过去24小时降序、已排程=未来24小时升序、第3~9列=过去24小时降序。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- `position: sticky` 在不同浏览器与容器组合下表现可能略有差异，需在目标演示环境实测冻结列效果。
- 当前第3~9列采用 pending 样本数据，若后端字段变动需同步调整映射。

下一步:
- 在 demo 仓库同步本次 UI 改造并记录新的 commit 映射（repo/branch/commit）。
- 根据客户反馈继续微调列宽、卡片密度与移动端可读性。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 更新 `data/samples/dashboard_published.json`、`data/samples/dashboard_scheduled.json`、`data/samples/dashboard_pending.json` 为 3/12 演示样本；第3~9列分类（社會事/大視野/兩岸/法庭事/消費/娛樂/心韓）均至少 3 条，且满足当前过去24小时展示窗口。
- [本仓库] 强化冻结列视觉隔离：前两列 sticky 区增加磨砂背景（`backdrop-filter`）与阴影分隔；在不支持磨砂时回退到主题背景，降低滚动时透底和误触。
- [本仓库] 侧边栏 Google Trends 接入 `https://trends.google.com/trending/rss?geo=HK`，增加 RSS 解析与缓存自动刷新（TTL=900s）；异常时回退本地 mock 数据。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与样本 JSON 文件无新增问题。
- pending 样本检查通过：7 个目标分类均为 3 条记录。

风险/阻塞:
- RSS 源可用性受网络与上游服务影响，短时异常会触发 fallback（已兜底）。
- 不同浏览器对 `backdrop-filter` 支持差异仍可能导致视觉细节不同，但不影响可用性。

下一步:
- 在 demo 仓库提交本次更新并补写实际 commit 映射（替换 `<待填新commit>`）。
- 客户实测后按反馈微调冻结列背景透明度与阴影强度。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 继续修复冻结区穿透问题：将前两列 sticky 改为“列级磨砂遮罩层（`::before`）+ 列间缝隙补层（`::after`）”的组合方案。
- [本仓库] 遮罩覆盖范围从列卡片扩展到整列与顶部标题区，减少横向滚动时第3列及之后内容在前两列区域可见/可点击的问题。
- [本仓库] 保留磨砂实现并强化参数（`saturate + blur`）；同时保留 `@supports` 回退与 dark/light 自适应背景，避免不支持环境下样式失效。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- `backdrop-filter` 仍受浏览器内核与硬件加速策略影响，不同设备上的磨砂观感可能有差异。

下一步:
- 在目标演示浏览器实测“冻结区可见性 + 点击命中”行为；如仍有穿透，再补一层冻结总面板遮罩（覆盖前两列总宽）。
- 同步 demo 仓库并回写 commit 映射。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 侧边栏 Google Trends 文案调整为两行：第一行“数据源：Google Trends RSS”（可点击跳转 Trends 页面），第二行“刷新时间：mm-dd hh:mm”并使用更小字号与弱化颜色。
- [本仓库] 趋势卡片主行改为仅展示“关键词（左）+ 搜索量（右）”，将时间移入详情区，避免主行信息拥挤导致显示不全。
- [本仓库] 接入 RSS 可用明细字段展示：展开后显示开始时间与最多 3 条 `ht:news_item` 细分信息（标题/来源/链接）；折线图字段在 RSS 中不可得，明确提示已略过。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- Streamlit 原生组件不易实现“点击卡片任意空白处展开 + 点击页面任意处自动收起”的前端级事件捕获；当前采用“展开详情/收起详情 + 单条展开状态”方案。

下一步:
- 若你确认要严格实现“点击卡片区域即展开、点击空白即收起”，下个迭代可改为自定义前端组件（streamlit-component）处理点击事件。
- 同步 demo 仓库并回写新 commit 映射。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 将侧边栏趋势区改为内嵌 HTML/CSS/JS 交互面板（`streamlit.components.v1.html`），实现“整卡点击展开、点击其他区域收起”的单选展开行为，样式更贴近 Google Trends。
- [本仓库] 数据源文案调整为两行：第一行“数据源：Google Trends RSS”（可点击链接到 Trends 页面），第二行“刷新时间：mm-dd hh:mm”（小字号弱化显示）。
- [本仓库] 卡片主行改为仅显示“关键词（左）+ 搜索量（右）”；展开后展示开始时间与 RSS 可用的 `news_item` 细分条目；折线图字段因 RSS 不提供，保留提示说明。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 该交互面板运行在 iframe 内，视觉和事件可控性明显提高，但与 Streamlit 原生组件的主题变量并非完全同步。

下一步:
- 在目标演示环境确认暗色主题下的色值观感，必要时微调卡片背景与文字对比度。
- 同步 demo 仓库并回写新 commit 映射。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 修复 `streamlit run src/dashboard/app.py` 启动时报错 `NameError: name 'source' is not defined`。
- [本仓库] 根因是 `_render_trends_widget` 的内嵌 JS 模板位于 Python f-string 中，`(${source})` 未做花括号转义；已改为 `(${{source}})`。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 内嵌 JS 模板后续若继续扩展，需注意 Python f-string 与 JS 模板语法的花括号转义冲突。

下一步:
- 重启 Streamlit 并复测侧边栏趋势卡片交互（展开/收起、链接跳转、明细展示）。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 按最新 UI 反馈调整侧边栏趋势区：移除“趋势折线图”提示文案，仅保留开始时间与趋势细分明细。
- [本仓库] 将趋势区标题并入内嵌面板，与“数据源/刷新时间”左对齐；两行元信息统一为更小字号与弱化颜色。
- [本仓库] 视觉重构：侧边栏整体改为磨砂背景并移除原黑底感；趋势容器同步使用磨砂底，卡片底色提亮以拉开层次。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 侧边栏与内嵌 iframe 的磨砂效果受浏览器/硬件加速支持影响，少数环境可能退化为实色背景（已设置 fallback）。

下一步:
- 在目标设备复测明暗主题下对比度与可读性；如需可继续微调卡片亮度和边框强度。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 调整趋势区布局与交互：将“数据源/刷新时间”移动到第10条后方底部小字区域；标题下改为排序图标入口（支持按开始时间/搜索量排序）。
- [本仓库] 排序逻辑与卡片右侧显示联动：按开始时间排序时右侧显示发布时间；按搜索量排序时右侧显示搜索量；展开后展示开始时间、搜索量与趋势细分。
- [本仓库] 新增居中圆形刷新按钮（图标），点击后强制重新拉取 RSS、更新本地趋势样本文件并刷新 UI。
- [本仓库] 继续优化视觉：侧边栏与趋势容器磨砂覆盖增强，卡片底色提亮，减轻滚动到底部时黑底突兀感。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 侧边栏磨砂与 iframe 背景融合仍受浏览器渲染策略影响，个别设备可能出现轻微色差。

下一步:
- 在客户常用设备复测“排序切换 + 刷新按钮 + 展开收起”体验，必要时再细调高度与间距。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 修复趋势区底部黑区残留：内嵌趋势面板改为 JS 自动上报 frame 高度（`streamlit:setFrameHeight`），随展开/收起动态调整，减少固定高度留白。
- [本仓库] 刷新按钮位置调整为紧贴列表底部（第10条后），保持居中圆形图标样式。
- [本仓库] 重做排序控件：去掉溢出感较强的 popover 触发器，改为“排序方式”小标签 + 简洁下拉选择（开始时间/搜索量）。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- `setFrameHeight` 依赖 Streamlit 前端消息机制，若后续 Streamlit 大版本行为变化，可能需要小幅调整事件触发时机。

下一步:
- 让用户复测不同窗口尺寸下的趋势区高度与按钮位置；若仍有空白，可在面板底部再加最小高度约束微调。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 修正趋势区“只显示一小节”问题：将内嵌趋势面板恢复为可视高度（560）并启用滚动，避免内容被裁切。
- [本仓库] 排序区改为同一行布局：左侧仅显示 `⇅` 图标，右侧显示下拉菜单（开始时间/搜索量），去掉“排序方式”文案。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 当前趋势区高度为固定值与滚动组合，极端小屏设备上仍可能需要后续再做分辨率自适应微调。

下一步:
- 用户复测手机/桌面布局；若仍有局部遮挡，再按设备断点调整趋势区高度和卡片间距。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 优化趋势卡片展开信息顺序：展开后顶部先显示“完整趋势词（加粗）”，再展示开始时间、搜索量与趋势细分明细。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 无新增阻塞。

下一步:
- 用户继续验收趋势区交互与视觉细节，按反馈做最后一轮样式收口。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 反转主面板分类筛选作用范围：`分類篩選` 仅作用于前两列（`已發佈`/`已排程`），不再影响第3~9列。
- [本仓库] 调整筛选候选来源为前两列数据集（published + scheduled），并同步更新筛选说明文案。
- [本仓库] 第3~9列（已出未排）恢复为固定按分类与时间展示，不受筛选项变化影响。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。

风险/阻塞:
- 若后续前两列与后七列分类枚举不一致，筛选器候选可能少于后七列展示分类（当前符合预期）。

下一步:
- 用户复测筛选交互：确认前两列随筛选变化、后七列保持不变。

日期时间(HKT): 2026-03-12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@0c4c03c47b3f9cc5f1e5b0a26d3ac430d2ea57ed
完成内容:
- [本仓库] 完成 demo UI 收口：九列主面板交互稳定，冻结列遮罩、筛选作用范围（仅前两列）与排序行为已按验收反馈落地。
- [本仓库] 完成趋势区改造：接入 RSS 自动更新、整卡展开/收起、排序切换、底部元信息与图标刷新按钮交互。
- [数据] 更新 3/12 演示样本数据（published/scheduled/pending/trends），保证演示可用性与时间窗口一致性。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与治理文档无新增问题。

风险/阻塞:
- 趋势区 iframe 在极端小屏下仍可能需要进一步压缩行高与边距。

下一步:
- 推送本次改动到 demo 仓库并回填实际 commit hash。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 更新 `data/samples/dashboard_published.json`、`data/samples/dashboard_scheduled.json`、`data/samples/dashboard_pending.json` 的演示假数据日期到 2026-03-13，并同步推进 `publish_time`、`updated_at`、`run_id`、`item_id`（pending）与标题日期标记。
- [本仓库] 调整 `src/dashboard/app.py` 九列看板的移动端样式：在竖屏场景下缩窄前两列 sticky 宽度、压缩卡片密度，并增强横向触控滚动配置，降低前两列遮挡第3列及之后内容的问题。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 无新增问题。
- 样本文件抽查通过：三份 JSON 的标题与时间字段已切换到 2026-03-13 语义。

风险/阻塞:
- 移动端 sticky 与磨砂遮罩在不同浏览器内核下仍可能有细微视觉差异，需在目标手机浏览器继续实测。

下一步:
- 在手机竖屏实测横向滑动体验；如仍感觉遮挡，可继续引入“手机端 sticky 宽度档位（紧凑/标准）”开关。