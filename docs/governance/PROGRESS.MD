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
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@b90e20d9bcf6b699fdca70db5a2366520d72400c
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

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@b90e20d9bcf6b699fdca70db5a2366520d72400c
完成内容:
- [demo仓库] 已将本次移动端 sticky 优化与 0313 样本数据更新推送到 `AiroGriefwind/fb-website-demo` 的 `main` 分支（commit: `b90e20d9bcf6b699fdca70db5a2366520d72400c`）。

验证结果:
- `git push public HEAD:main` 成功，远端由 `a883ddc` 更新至 `b90e20d`。

风险/阻塞:
- 若手机继续出现超时，问题将主要位于局域网连通、防火墙或 Streamlit 监听策略，而非代码版本。

下一步:
- 排查并固定 `http://<电脑局域网IP>:8501` 的手机访问链路（监听地址、防火墙、端口放行）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 调整九列看板卡片宽度策略：将卡片宽度从“随列拉伸（`width: 100%`）”改为“固定宽度变量”。
- [本仓库] 前两列 sticky 卡片设为更宽（`--card-width-main`），后七列设为较窄（`--card-width-category`），并在桌面/平板/手机断点分别给出固定值。
- [本仓库] 标题改为单行省略样式（`white-space: nowrap; text-overflow: ellipsis; overflow: hidden;`）。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 标题单行后信息密度提高，但长标题可见字数减少；如需兼顾可读性可后续增加 hover tooltip 或二级详情。

下一步:
- 根据你电脑端与手机端截图反馈微调 `--card-width-main` / `--card-width-category` 数值（建议每次 6~10px 步进）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 按反馈移除“前两列卡片更宽”策略，九列统一使用单一列宽变量 `--col-width`。
- [本仓库] 将看板栅格改为 `grid-template-columns: repeat(9, var(--col-width))`，并同步 sticky 第2列偏移计算为 `var(--col-width) + gap`。
- [本仓库] 卡片宽度恢复与列宽绑定（`width: 100%`），列头与卡片统一宽度，不再出现前两列列头明显宽于卡片的问题。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 统一列宽后，桌面端首两列可视信息密度相较上一版略降（属于预期取舍）。

下一步:
- 依据你下一轮截图反馈，仅微调统一列宽变量 `--col-width`（桌面/平板/手机三个断点）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 为前两列 sticky（`已發佈`/`已排程`）新增列级收起交互：点击列头可将整列折叠为最左侧 sticky 图标，再次点击恢复展开。
- [本仓库] 列头交互文案与图标升级：展开态显示“`⇅ + 列名 + <<<`”提示可收起；收起态保留图标，hover 时图标切换为“`>>>`”提示可展开。
- [本仓库] 折叠布局通过 CSS 状态控制实现：动态调整前两列宽度变量（`--col1-width`/`--col2-width`）与第2列 sticky 偏移，保证收起后第3列内容可见面积提升。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 当前折叠状态为前端会话内状态（页面刷新后重置）；如需跨刷新持久化，需后续接入 `st.session_state` 或 URL 参数同步。

下一步:
- 让你在桌面端与手机端实测“收起/展开 + 横向滑动”组合体验，按反馈微调折叠态图标尺寸和列宽。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 修复分类筛选组件告警：移除 `st.multiselect` 的 `default` 与 `Session State` 同时赋值冲突，仅通过 `key` + `st.session_state` 初始化选中项。
- [本仓库] 修复前两列列头点击无反应：折叠样式选择器改为 `board-root:has(#toggle-colX:checked)`，并将折叠状态输入与看板放在统一容器下，避免 HTML 结构层级导致的 sibling 选择失效。
- [本仓库] 交互图标从示例符号替换为更贴切的横向控制图标 `⟷`；收起态 hover 仍显示 `>>>` 作为展开提示。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 折叠交互依赖 CSS `:has`，在现代浏览器兼容良好；若遇到极旧浏览器需降级为纯 Streamlit 按钮控制。

下一步:
- 请你在目标浏览器实测列头点击与折叠/展开反馈；若需要我可再把“收起态仅显示图标”区域做得更窄（例如 30px）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 按反馈将“隐藏前两列”入口从列头迁移到看板左侧独立控制栏，避免折叠后在原两列位置保留 sticky 小残影挡视野。
- [本仓库] 为两列使用不同图标：`已發佈=📰`、`已排程=📅`，并保留 hover 提示（隐藏态提示 `>>>`，显示态提示 `<<<`）。
- [本仓库] 调整折叠布局逻辑：隐藏时直接 `display:none` 对应列，并按“隐藏第1列/隐藏第2列/两列都隐藏”三种状态切换 grid 模板，最大化第3列以后可视区域。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 控制栏图标使用 emoji，不同系统字体渲染风格会略有差异；如需统一可替换为纯 SVG/字符图标。

下一步:
- 让你在手机端验证“两列全隐藏”时的实际可视宽度提升，必要时再压缩左侧控制栏宽度（40→34 或更小）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4456ad4
完成内容:
- [本仓库] 保留左侧独立控制栏的同时，恢复前两列列头可点击交互：列头左侧显示对应图标与列名（`📰 已發佈`、`📅 已排程`），右侧显示 `<<<` 提示。
- [本仓库] 为前两列显隐增加动效：隐藏时向左平移并渐隐，显示时向右回位并渐显；同时列宽变量平滑过渡，减少突兀跳变。
- [本仓库] 前两列列头与左侧控制栏共享同一显隐开关（checkbox），保证两处入口行为一致。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 列宽过渡依赖浏览器对 `grid-template-columns` 动画支持；在少数旧浏览器上可能退化为无动画切换，但功能不受影响。

下一步:
- 让你在目标浏览器复测“列头点击 + 左侧按钮点击”一致性与动画顺滑度，必要时微调动画时长（当前 0.24s）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@e662769
完成内容:
- [本仓库] 修复移动端左侧控制栏提示常驻问题：将提示浮层限制为“仅支持 hover 的设备”显示，在触屏设备禁用悬浮提示，避免点击后长期停留。
- [本仓库] 强化前两列与后续列的等宽约束：列容器统一 `width: var(--col-width)`，并为前两列补齐副标题占位行，改善与后续两行列头的视觉一致性。
- [本仓库] 修复前两列间穿透感：提高 sticky 遮罩不透明度与层级（z-index），并增强列间分隔阴影，减少卡片内容在列缝处透出/误触。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- sticky 磨砂与阴影观感仍受浏览器渲染内核差异影响，极少数设备上可能有轻微深浅差别。

下一步:
- 让你复测手机端提示行为与前两列遮挡效果；若需要可进一步降低遮罩透明度波动（改为纯实色背景）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@e662769
完成内容:
- [本仓库] 修复前两列宽度与穿透回归问题：将第1/2列宽度绑定到动态变量 `--col1-width`/`--col2-width`，避免隐藏动画时列轨道为 0 但列元素仍保持 `--col-width` 导致重叠。
- [本仓库] 修正第2列 sticky 偏移为基于第1列动态宽度（`left: calc(var(--col1-width) + gap)`），保证第1列收起后第2列不会漂移遮挡。
- [本仓库] 增加隐藏态内容可见性保护（`visibility: hidden`）与统一 `box-sizing`，减少列缝穿透和宽度不一致观感。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 仍依赖 `:has` 支持来驱动纯 CSS 状态联动；旧浏览器可能仅退化动效，不影响基本可用性。

下一步:
- 推送到 demo 仓库后让你在桌面/手机复测“首两列等宽 + 无穿透 + 折叠动画”三项。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4848673
完成内容:
- [本仓库] 继续修复前两列穿透与宽度观感问题：将列容器从 `overflow: hidden` 调整为 `overflow: visible`，确保 sticky 列的列缝遮挡层（`::after`）不会被裁切。
- [本仓库] 隐藏动画状态下对前两列单独回设 `overflow: hidden`，避免折叠过程中卡片内容外溢。
- [本仓库] 统一列头结构：前两列补齐副标题占位行（`&nbsp;`），与后七列“列名 + 次级行”保持一致，减少“前两列看起来更窄”的视觉偏差。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 视觉层的磨砂 + 阴影遮挡仍受浏览器渲染差异影响，极少数环境可能存在轻微色边。

下一步:
- 让你在本地与线上同时复测“第一二列间穿透”与“列头宽度一致性”，必要时再切换为纯实色遮挡以彻底消除色边。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@2c2bbbb
完成内容:
- [本仓库] 接入栏目色彩映射（社會事/大視野/兩岸/法庭事/消費/娛樂/心韓）并生成浅色版（约 33% 强度）样式 token，用于看板配色统一。
- [本仓库] 完成两类着色：`已發佈/已排程` 中卡片按贴文分类上浅色底；第3~9列各栏位列头按对应分类上浅色底，保留可读性。
- [本仓库] 为分类筛选器增加按分类自动着色：通过前端 DOM 监听给 multiselect 已选标签上对应浅色底，便于编辑同事快速识别类别。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 筛选器标签着色依赖 Streamlit 前端 DOM 结构（`data-baseweb=tag`）；后续若 Streamlit 升级改动 DOM，需要同步微调选择器。

下一步:
- 让你在线上/本地观察颜色浓度是否合适；若偏浅或偏深，可统一调整色彩混合强度（当前 33% / 卡片 22%）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@2c2bbbb
完成内容:
- [本仓库] 按反馈微调分类浓度：仅提升 `法庭事/消費/心韓` 的浅色混合强度，增强三者在列头、卡片底色与筛选标签中的区分度。
- [本仓库] 新增分类级浓度覆盖配置 `CATEGORY_INTENSITY_OVERRIDES`，以便后续按单分类继续微调而不影响其他分类颜色。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 若在暗色主题下仍感觉色差不够，可进一步提高 `header/card` 比例（每次建议 0.03~0.05 步进）。

下一步:
- 让你在线上确认三类区分度；如需可继续单独拉高 `法庭事` 或 `心韓`，不影响其他分类。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@6f70d2e
完成内容:
- [本仓库] 新增拖拽排程主流程（MVP）：`已出未排` 卡片支持鼠标拖拽 / 触屏长按后拖放到 `已排程` 列，释放后进入排程时间设置弹窗。
- [本仓库] 新增排程弹窗（`st.dialog`）：支持日期 + 小时 + 分钟设置，分钟仅允许 `00/05/10/.../55`（5 分钟粒度）。
- [本仓库] 新增本地样本写回：确认排程后从 `dashboard_pending.json` 移除目标贴文并写入 `dashboard_scheduled.json`，自动更新 `publish_time` 与 `updated_at`，随后刷新 UI 按新时间重排。
- [本仓库] 增加拖放桥接脚本：在前端监听拖放并通过 URL query 参数回传 `item_id` 触发后端弹窗流程。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 当前拖放桥接依赖前端 DOM 结构与浏览器拖放事件；不同移动端浏览器的长按触发体验可能有细微差异，已提供基础长按拖放兜底。
- 若启用 `DASHBOARD_API_BASE_URL`（API 模式），本地样本写回会被禁用并给出提示。

下一步:
- 让你在桌面与手机实测拖放命中、弹窗唤起与写回结果；按反馈微调长按时长与 drop zone 命中范围。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@6f70d2e
完成内容:
- [本仓库] 修复拖放后“无事发生”问题：增强拖放桥接的 item_id 传递链路，采用 `dataTransfer`（`application/x-item-id` + `text/plain`）与全局拖拽状态双通道兜底。
- [本仓库] 补强 drop 事件处理（`stopPropagation`）并兼容 query 参数读取返回 `list|string` 两种格式，确保拖放后能稳定触发排程弹窗。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 拖放回传仍依赖浏览器对 iframe/parent URL 变更策略；若个别环境阻止父页面导航，需改为 Streamlit 自定义组件双向通信方案。

下一步:
- 让你复测桌面拖放“松手即弹窗”；若仍不触发，将切换为同页原生拖放组件（无 parent URL 跳转依赖）。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@6f70d2e
完成内容:
- [本仓库] 为拖放排程链路加入详细 debug 日志：前端在浏览器 console 输出初始化、卡片绑定、dragstart/drop、item_id 解析、URL 跳转等关键节点。
- [本仓库] 增加后端 query 参数接收调试提示：页面显示 `schedule_pick raw/parsed`，帮助定位“前端 drop 已触发但后端未接收”的问题。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 当前 debug 输出较多，便于排障；问题定位完成后建议收敛或加开关控制。

下一步:
- 由你执行一次拖放并提供 console 输出日志，基于日志定位最终卡点并修复。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@6f70d2e
完成内容:
- [本仓库] 基于 debug 日志定位到拖放回传失败根因：`components.html` iframe 被 sandbox 限制，无法直接导航父页面（`window.parent.location.href`）。
- [本仓库] 将回传机制改为“无导航”链路：拖放后通过 `window.parent.history.replaceState` 写入 `schedule_pick` 查询参数，再自动点击隐藏的 Streamlit 按钮触发 rerun，以拉起排程弹窗。
- [本仓库] 保留 debug 输出，新增“已写入 query 参数/已触发隐藏按钮”日志，便于确认链路是否完整触发。

验证结果:
- `python -m py_compile src/dashboard/app.py` 通过。
- `read_lints` 检查 `src/dashboard/app.py` 与 `docs/governance/PROGRESS.MD` 无新增问题。

风险/阻塞:
- 若后续 Streamlit DOM 结构变更导致隐藏按钮选择器失效，需同步调整 `.st-key-drag_drop_commit button` 定位规则。

下一步:
- 让你复测拖放后是否可直接弹出排程对话框；如仍失败，再升级为自定义 streamlit component 双向通信。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4ddf472
完成内容:
- [本仓库] 更新 `docs/governance/TECHSTACK.MD` 的 Streamlit 技术条目，补充当前已实现能力清单与函数映射（页面状态、弹窗、拖拽排程、RSS 解析、样本读写、前端组件桥接、样式系统）。
- [本仓库] 对 `src/dashboard/app.py` 现状进行结构复盘（函数分布与职责边界），为后续模块化拆分提供依据。

验证结果:
- 文档内容已更新并与当前代码实现一致，可用于快速理解现有 dashboard 能力与技术路径。

风险/阻塞:
- `app.py` 当前体量较大（1500+ 行），若继续叠加功能，维护成本和回归成本会持续上升。

下一步:
- 按“数据层 / 视图层 / 前端桥接层 / 业务动作层”拆分 `app.py` 为多模块，并保留 `src/dashboard/app.py` 作为薄入口。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4ddf472
完成内容:
- [本仓库] 启动 `app.py` 第一阶段拆分：新增 `src/dashboard/config.py`（常量）、`data_utils.py`（数据加载/RSS/排序）、`media_utils.py`（时间与缩略图工具）、`style_utils.py`（分类配色）、`scheduling_utils.py`（待排程->已排程写回）。
- [本仓库] `src/dashboard/app.py` 改为调用上述模块（保留原函数名作为兼容包装），实现“行为不变”的前提下完成核心工具层拆分。
- [本仓库] 保留 `src/dashboard/app.py` 为页面装配入口，降低后续二阶段拆分风险。

验证结果:
- `python -m py_compile` 覆盖 `app.py` 与 5 个新模块全部通过。
- `read_lints` 检查拆分涉及文件无新增问题。

风险/阻塞:
- 当前仍保留部分兼容包装函数（为确保零行为回归）；下一阶段可继续下沉渲染函数，进一步缩短 `app.py`。

下一步:
- 第二阶段拆分渲染层：优先迁移 `board/trends/settings` 视图函数与前端脚本模板，`app.py` 收敛为路由与编排入口。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4ddf472
完成内容:
- [本仓库] 完成第二阶段核心拆分：新增 `src/dashboard/board_view.py`，承接主看板渲染、拖拽排程对话框与列布局逻辑；`app.py` 改为调用 `render_today_board()`。
- [本仓库] 新增 `src/dashboard/frontend_templates.py`，集中管理前端 JS 模板（分类筛选标签着色脚本、拖放排程桥接脚本）。
- [本仓库] `app.py` 移除已迁出的 board 相关大段实现，保留为主入口编排层（页面配置 + sidebar/settings + board 调用）。

验证结果:
- `python -m py_compile` 覆盖 `app.py`、`board_view.py`、`frontend_templates.py` 及 dashboard 子模块全部通过。
- `read_lints` 检查 `src/dashboard/` 无新增问题。

风险/阻塞:
- 目前 `trends/settings` 仍在 `app.py`，后续可继续拆到 `trends_view.py` / `settings_view.py`，进一步降低主文件复杂度。

下一步:
- 第三阶段拆分：迁移 sidebar/trends/settings 视图函数与样式片段，`app.py` 最终收敛为薄入口。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4ddf472
完成内容:
- [本仓库] 完成第三阶段拆分：新增 `src/dashboard/sidebar_view.py`，迁移 `sidebar/trends/settings` 相关 UI 与交互函数。
- [本仓库] 新增 `src/dashboard/frontend_templates.py` 承载前端模板后，继续由 `board_view.py` / `sidebar_view.py` 复用，减少主入口中的内嵌脚本体积。
- [本仓库] `src/dashboard/app.py` 收敛为薄入口（仅保留 page config、标题、health、模块编排调用）。
- [本仓库] 修复拆分过程中的 `app.py` 字符串编码异常，恢复页面标题与 caption 文案。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 所有模块通过。
- `read_lints` 检查 `src/dashboard/` 与治理文档无新增问题。

风险/阻塞:
- 趋势卡片 HTML/CSS/JS 仍为内联模板，后续可继续抽为独立模板文件或组件以提升可维护性。

下一步:
- 进行一次手工回归：设置弹窗、趋势刷新、拖拽排程（桌面/移动）三条主链路验证。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@4ddf472
完成内容:
- [本仓库] 按需求更新 `docs/governance/STARTUP.MD`：在 `feature/bot-ui-ops` 下新增 3 组后续对话可复用的“开场白提示词”。
- [本仓库] 新增主题分别覆盖：`Json -> PostgreSQL`（并发与审计）、`登录与访问控制`、`假数据 -> API 真数据`，并统一写入阅读前置、目标、约束与进度回写要求。

验证结果:
- 文档结构与现有治理风格一致，可直接复制给后续 LLM 对话使用。

风险/阻塞:
- 若后续职责边界变化（例如新增独立 API 服务目录），需同步更新提示词中的“重点目录/改动范围”约束。

下一步:
- 在下一轮任务启动时使用对应提示词，确保各子任务的职责边界与交付标准一致。

日期时间(HKT): 2026-03-13
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@76c2fcd
完成内容:
- [本仓库] 按最新需求调整卡片配色显示模式：`已發佈/已排程` 两列中，仅 `娛樂` 分类卡片保留浅色底，其余分类统一白底；`已出未排` 七列保持原分类配色不变。
- [本仓库] 颜色逻辑采用“覆盖而非删除”策略：保留分类色类名与样式 token，便于后续在设置中扩展用户可切换显示模式。

验证结果:
- `python -m py_compile src/dashboard/board_view.py` 通过。
- `read_lints` 检查 `src/dashboard/board_view.py` 与治理文档无新增问题。

风险/阻塞:
- 当前显示模式为硬编码默认值；若后续支持用户切换，需增加 session_state 配置项并在 CSS 生成阶段分支。

下一步:
- 由你在线上确认“已排程去彩色（仅娛樂保留）”观感；如需可再调娛樂底色浓度。

日期时间(HKT): 2026-03-18 18:44
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 按用户反馈彻底移除九列看板中的“拖拽排程”链路：删除 draggable 卡片、drop zone 高亮、隐藏提交按钮、前端拖拽脚本与相关 debug 提示。
- [本仓库] 将排程触发改为“点击第3~9列（已出未排）卡片顶部 12 点位 `📅` 图标按钮”，点击后通过 `schedule_pick` 打开原有排程时间弹窗。
- [本仓库] 同步更新 `docs/governance/TECHSTACK.MD` 的 Streamlit 当前实现描述，移除拖拽叙述并改为 icon 触发排程说明。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/board_view.py`、`src/dashboard/frontend_templates.py` 无新增问题。

风险/阻塞:
- 卡片顶部 `📅` 按钮与卡片本体链接并存，移动端需继续实测误触率与可点面积是否满足编辑同事习惯。

下一步:
- 由你在 demo 部署环境验证“第3~9列点击 `📅` 即拉起排程弹窗”主链路；若需要可再放大按钮尺寸或扩展到整卡点击排程。

日期时间(HKT): 2026-03-18 21:56
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 排程窗口参数化：在 `設置` 中新增“排程窗口（分钟）”可选项（5/10/15/20/30），排程弹窗分钟选项与默认时间对齐该设置。
- [本仓库] 新增“锁定窗口”能力：排程弹窗加入 `🔒 锁定` 开关；`已排程` 卡片顶部（12 点位）新增 `🔒` 可切换按钮（点击锁定/取消锁定）。
- [本仓库] 更新排程写入规则：锁定贴文不参与顺延；若目标时间窗口已被锁定则拒绝写入；插入新排程时对后续未锁定贴文按窗口顺延并自动避开锁定窗口。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/board_view.py`、`sidebar_view.py`、`scheduling_utils.py`、`media_utils.py`、`frontend_templates.py` 无新增问题。

风险/阻塞:
- 当前锁定状态仅落在本地样本数据字段 `is_locked`；切换到 API 模式时需后端同步支持该字段与冲突校验语义。

下一步:
- 在 demo 环境复测三条链路：窗口粒度切换、锁定窗口拒绝写入、顺延时跳过锁定贴文。

日期时间(HKT): 2026-03-18 22:02
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 设置弹窗新增“确认排程窗口”按钮：将窗口选择改为草稿值（`cfg_schedule_window_minutes`），仅点击确认后写入生效值并触发 rerun 刷新。
- [本仓库] 修复“点排程按钮却弹设置弹窗”问题：`app.py` 调整为先渲染看板再判定设置弹窗；并在排程/锁定动作进入时强制关闭设置弹窗状态。
- [本仓库] 增加对话框并发保护：`render_settings_dialog_if_needed()` 在排程弹窗打开时直接跳过，避免 Streamlit 的“同轮仅允许一个 dialog”异常。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/app.py`、`board_view.py`、`sidebar_view.py` 无新增问题。

风险/阻塞:
- 若用户通过浏览器地址栏手工注入历史 query 参数，仍可能触发非预期弹窗流；当前已在处理后清理 `schedule_pick/lock_toggle` 参数以降低风险。

下一步:
- 在 demo 环境重点回归“设置确认后刷新粒度 + 排程入口不串弹窗”两条链路。

日期时间(HKT): 2026-03-18 22:12
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 优化顺延算法为“局部挤压链”：只从目标窗口开始逐窗向后传递冲突，不再无差别推动所有后续贴文；当下一窗口为空时在此终止，不影响更后面的排程。
- [本仓库] 在 `已排程` 卡片新增右上角 `🔙` 入口，支持“取消排程并返回已出未排”；返回后恢复 `review_status=waiting`，写回 pending 数据集。
- [本仓库] 扩展前端桥接参数：新增 `unschedule_pick` 动作通道及隐藏提交按钮，保持与 `schedule_pick/lock_toggle` 同样的当前页无跳转交互。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/app.py`、`board_view.py`、`sidebar_view.py`、`scheduling_utils.py`、`frontend_templates.py` 无新增问题。

风险/阻塞:
- 取消排程后当前实现将贴文 `publish_time` 更新为“当前时间”，确保能回到已出未排列可见窗口；若后续需要保留原时间语义，可改为额外字段记录“原排程时间”。

下一步:
- 在 demo 环境回归“9:30 挤到 9:45 但 10:00 不动”的窗口链路与 `🔙` 返回链路（分类归位 + 可再次排程）。

日期时间(HKT): 2026-03-18 22:18
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 修复设置/排程串弹窗：点击 `設置` 时强制关闭排程弹窗状态，并在排程弹窗渲染函数中增加“设置打开即跳过”的硬保护。
- [本仓库] 修复时间窗口下拉：对“所选日期=今天”场景仅展示未来时间槽（例如当前 10:15 不再显示 10:10 及更早）；无可用槽时自动切到次日。
- [本仓库] 增加后端兜底校验：排程写入阶段拒绝过去时间，即便前端状态异常也不会写入历史窗口。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/app.py`、`board_view.py`、`sidebar_view.py`、`scheduling_utils.py` 无新增问题。

风险/阻塞:
- 当前“过去时间过滤”以 HKT 当前时间为准；若后续引入多时区协作，需要在设置层明确时区提示与换算策略。

下一步:
- 在 demo 环境复测“点设置不串排程 + 今天仅可选未来窗口”两条关键链路。

日期时间(HKT): 2026-03-18 22:25
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 新增“排程影响报告”折叠 UI（位于分类筛选器下方）：折叠标题展示“顺延数量 + 锁定跳过数量 + 锁定时间列表”。
- [本仓库] 排程核心函数返回本次影响明细：顺延文章（标题/原时间/新时间）与因锁定跳过的文章（标题/锁定时间），供 UI 展开后查看。
- [本仓库] 成功排程后将影响明细写入 `st.session_state`，确保用户可即时回顾本次窗口挤压的实际波及范围。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/board_view.py`、`scheduling_utils.py` 无新增问题。

风险/阻塞:
- 当前报告展示的是“最近一次排程动作”；若后续需要跨会话审计，建议将该明细同步写入运行日志或后端事件表。

下一步:
- 由你在 demo 环境确认折叠标题统计与展开明细是否满足编辑团队阅读习惯（必要时可改为表格样式）。

日期时间(HKT): 2026-03-18 22:32
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 修复线上 `🔒` 图标显示异常：将已排程卡片顶部锁按钮从 emoji 字形改为内嵌 SVG path，避免不同系统字体缺字导致空白圆按钮。
- [本仓库] 同步微调锁按钮样式（可见度、锁定态底色、移动端尺寸）以保证线上/本地视觉一致性。

验证结果:
- `python -m py_compile src/dashboard/board_view.py` 通过。
- `read_lints` 检查 `src/dashboard/board_view.py` 无新增问题。

风险/阻塞:
- 无新增阻塞；该方案不依赖系统 emoji 字体，跨平台稳定性更好。

下一步:
- 推送到 demo 仓库并让线上刷新确认锁图标可见。

日期时间(HKT): 2026-03-25 15:00
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 完成 `src/dashboard/api_smoke_test_app.py` 冒烟测试页：覆盖并逐一跑通 `login/posts/fb_published/fb_scheduled/fb_publish/fb_update/fb_delete`，支持展示“请求体 + 完整HTTP请求 + 响应JSON”。
- [本仓库] 完成鉴权链路排障并沉淀结论：登录阶段使用网关 Basic 通过入口；后续业务接口使用 Bearer token（并根据接口行为保留必要 cookie）；已通过独立 `http.client` 脚本与 Streamlit 冒烟页双路径验证。
- [本仓库] 将前置读接口接入 demo 主页面数据流：页面加载自动登录并拉取 `fb_published/fb_scheduled/posts(各分类)`，写回 `data/samples/dashboard_published.json`、`dashboard_scheduled.json`、`dashboard_pending.json`，替代原假数据来源参与看板渲染。
- [本仓库] 增加对接测试开关（设于側栏設置）：`分类归一化测试模式` 与 `渲染兜底测试模式`，默认关闭，便于测试站调试与正式版隔离。
- [本仓库] 修复若干接入阶段 UI 问题：卡片/列宽统一约束、图片固定尺寸与坏链回退 `Dummy1`、看板主渲染切换 `components.html` 以规避 HTML 原文泄露。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/` 相关模块通过。
- `read_lints` 检查 `src/dashboard/app.py`、`live_api_sync.py`、`board_view.py`、`sidebar_view.py`、`api_smoke_test_app.py` 无新增问题。
- 冒烟验证结论：`Get Published`、`Get Scheduled`、`Get Category Posts` 均可返回真实数据；`Publish/Update/Delete` 在冒烟页可发起并返回 API 结果。

风险/阻塞:
- 业务环境对 `Authorization` 与网关策略存在历史差异（Basic/Bearer 分工需以当前环境实测为准）；后续接入写操作时仍需保留超时、重复点击与失败重试的保护。
- 真数据图片源存在失效/防盗链场景，已做占位兜底，但仍建议后续接入后端缩略图代理以提升稳定性。

下一步:
- 进入 FB 写操作 API 集成阶段：将 `fb_publish` 绑定“已出未排 -> 排程”动作，将 `fb_update`（✏️）接入已发布/已排程卡片，将 `fb_delete`（🗑️ / 已排程🔙确认）接入对应弹窗流程，并补充操作日志、loading 态、防重复提交与错误提示。

日期时间(HKT): 2026-03-25 23:20
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 完成 FB 写操作主链路接入：`已出未排` 排程确认调用 `fb_publish`；`已排程/已发布` 新增 `✏️` 调用 `fb_update`；`已发布🗑️` 与 `已排程🔙` 确认后调用 `fb_delete`。
- [本仓库] 新增 `src/dashboard/fb_action_client.py`：统一封装 login/token/cookie 与 `fb_publish/fb_update/fb_delete` 请求，输出统一结果结构并记录日志到 `logs/dashboard_fb_actions.jsonl`（敏感头已脱敏）。
- [本仓库] 数据映射增强（`live_api_sync.py`）：补齐 `post_id/post_link_id/post_link_type/post_message/image_url/post_mp4_url`；支持 fanpage 过滤规则（目标 fanpage 已出现 link+post_link_id 时从“已出未排”隐藏）；补齐排程图缺图回填。
- [本仓库] 交互与可靠性修复：已排程修改时间改为“小时/分钟/日期下拉 + 粒度联动 + 禁过去 + 锁窗口校验”；慢请求统一改为“关闭弹窗后在主页提示区显示 loading/结果”；修复 Streamlit 多 dialog 冲突。
- [本仓库] 设置持久化升级：新增 `data/samples/dashboard_settings_state.json`，支持按 token-hash 会话键保存测试设置；设置弹窗改为“确认/返回”，返回支持未保存修改提示与放弃确认。
- [本仓库] 修复删除命中关键字段：`fb_delete/fb_update` 的 `post_id` 改为 CMS 文章 `ID` 语义；通过 posts 数据构建 `post_link_id/post_link -> CMS ID` 映射回填，避免误用 FB page id 导致删除未生效。
- [本仓库] 优化弹窗前等待：仅打开操作弹窗时跳过一次页面级 API 同步，避免点击 `📅` 后无必要等待。

验证结果:
- `python -m py_compile` 覆盖 `src/dashboard/app.py`、`board_view.py`、`live_api_sync.py`、`sidebar_view.py`、`fb_action_client.py` 通过。
- `read_lints` 检查上述改动文件无新增问题。
- 本地回归链路覆盖：排程弹窗打开、修改弹窗时间控件、删除确认流程、设置确认/返回与未保存提示、主页级 loading 与结果提示。

风险/阻塞:
- 线上环境若 Basic/Bearer 网关策略与测试站不一致，写接口仍可能出现鉴权差异；需以上线实测结果为准并据此固定 headers 策略。
- `posts -> fb_scheduled/fb_published` 的 CMS ID 回填依赖 `post_link_id`/`post_link` 一致性；若后端字段规则变动，需同步更新映射策略。

下一步:
- 先在线上部署并验证真实 API（publish/update/delete + 错误提示 + 日志记录）全链路。
- 线上验证通过后，再进行本地 UI 细节收口（按钮密度、文案、微交互和移动端观感）。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / GPT-5.4
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@<待填新commit>
完成内容:
- [本仓库] 继续收口真实 API 看板链路：补强 `src/dashboard/live_api_sync.py` 的缩略图回填策略，修复“已出未排 -> 已排程”后缩略图掉回 `Dummy1` 的问题。
- [本仓库] 回滚不再需要的 VPN 接入尝试，移除 `vpn_helper` 依赖，恢复 `app.py` / `live_api_sync.py` / `api_smoke_test_app.py` 的稳定导入路径。
- [本仓库] 围绕真实写操作体验修复主交互：增加 `fb_publish/fb_update/fb_delete` 的会话级自愈、前端桥接稳定性修正、动作期间跳过全量同步，以及“先关闭弹窗再进入执行”的过渡页机制。
- [本仓库] 将“锁定窗口拒绝写入 / 未锁定窗口局部顺延”规则接到当前 API 排程路径，并在同步后按 `post_link_id/Post URL` 回填 `is_locked`，避免锁定状态被真数据同步覆盖。
- [治理] 新增本地运行态忽略规则：`logs/`、`debug-*.log`、`tmp_schedule_*.js`、`.streamlit/`、`data/samples/dashboard_settings_state.json` 不再进入版本控制；`dashboard_ui_debug.jsonl` 保留本地排障用途。

验证结果:
- `python -m py_compile` 已覆盖 `src/dashboard/app.py`、`board_view.py`、`live_api_sync.py`、`frontend_templates.py`、`api_smoke_test_app.py` 等本轮改动文件并通过。
- `read_lints` 检查本轮改动文件无新增问题。
- 本地联调已覆盖：排程弹窗打开与确认、取消排程、修改排程、缩略图回填、锁定图标显示、动作期间主页 loading/结果提示。

风险/阻塞:
- 当前过渡页与动作执行仍属于整页 rerun 模式，体感已改善但尚未达到“只刷新单列”的理想状态；若继续追求秒级体验，需进一步重构为局部数据拉取或前端组件化列表。
- `is_locked` 当前仍是前端/本地同步层保存的附加状态，若未来切到真正多用户后端，需要把锁定语义迁入服务端存储与并发校验。

下一步:
- 将本次 dashboard 真实 API 写操作与交互修复推送到 demo 仓库并回填实际 commit hash。
- 下一轮重点重构“局部刷新体验”：评估按列/按动作最小化拉取，减少整页 rerun 与同步等待。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / GPT-5.4
分支/worktree: feature/bot-ui-ops（本仓库） | demo仓库: AiroGriefwind/fb-website-demo/main@65d9bd4
完成内容:
- [治理] 确认 demo 远端 `main` 在 `b136b44` 之后追加的 API 调试提交（如 `dafac41/4efa067/898f0bb/627f1e3/e9463e8`）不再作为交付基线，当前以本地分支 `feature/bot-ui-ops` 的 `65d9bd4` 为准。
- [治理] 为避免丢失审计线索，保留历史进度记录不删除；改为追加“基线切换记录”，明确后续 demo 展示和部署均以本地修复后的 dashboard 交互与真实 API 链路为准。
- [治理] 计划执行 demo 远端保护性备份后，再以 `--force-with-lease` 对齐 `public/main` 到本地基线。

验证结果:
- 本地 `HEAD` 已确认是 `65d9bd4`，且 `b136b44` 为其祖先提交。
- 后续 API 调试提交经核对均不在当前本地分支历史中，说明 demo 远端与本地基线已发生分叉。

风险/阻塞:
- 覆盖 demo 远端 `main` 需要改写该仓库公开分支历史；虽会先创建备份分支，但其他协作者若基于旧 `main` 开发，需要在拉取时重新对齐。

下一步:
- 先推送一个 demo 远端备份分支保存旧 `main` 状态。
- 再把 demo 远端 `main` 安全对齐到本地 `65d9bd4`，并回填新的远端 commit 记录。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 新增独立后端入口 `src/dashboard_api/`：抽离 `CmsActionClient`（无 Streamlit 依赖）与看板服务层，统一承接 `publish/update/delete/toggle-lock` 动作边界，并复用现有同步链路回写样本数据。
- [本仓库] 定义最小 HTTP API 契约并实现 `FastAPI` 服务：`GET /api/board/columns`（支持 `include=scheduled,pending:分類` 局部拉取）、`POST /api/actions/publish|update|delete|toggle-lock`、`GET /api/health`。
- [本仓库] 新增独立前端看板 MVP `frontend/board/index.html`（Alpine.js）：覆盖九列展示、排程/修改/取消排程/锁定核心动作，并在动作后按受影响列执行局部 refetch（scheduled + 对应 pending 分类）。
- [本仓库] 明确 Streamlit 迁移角色：`src/dashboard/app.py` 调整为“设置/调试控制台”入口，新增指向独立看板的跳转按钮（`DASHBOARD_BOARD_URL` 可配置）。
- [本仓库] 依赖补齐：`requirements.txt` 增加 `fastapi`、`uvicorn`；新增 `src/dashboard_api/run.py` 作为本地启动脚本。

验证结果:
- 本地冒烟通过：`/api/health`、`/api/board/columns?include=scheduled,pending:娛樂`、`/board/` 均可访问并返回预期内容。
- Python 导入检查通过：`from src.dashboard_api.server import app` 可正常加载路由。
- `read_lints` 检查 `src/dashboard_api/` 与 `src/dashboard/app.py` 无新增诊断错误。

风险/阻塞:
- 当前写动作成功后仍使用既有 `sync_live_data_to_sample_files` 刷新读模型，速度较旧版已改善，但尚未接入真正的增量读模型存储。
- `is_locked` 目前仍是样本层状态语义；多用户并发场景仍建议尽快迁移到共享存储/数据库。

下一步:
- 将局部刷新策略继续细化到时间区段级别（有顺延时仅刷新受影响窗口），并补充前端乐观更新与失败回滚。
- 逐步把 Streamlit 页面的业务动作切到新 HTTP API，仅保留设置与调试能力。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板 `frontend/board/index.html` 完成 UI 第一轮重构：接入真实 `Dummy1.png` 缩略图路径、九列卡片样式优化、前两列 sticky 冻结、侧边栏可收起到左侧贴边并支持一键展开。
- [本仓库] 侧边栏功能对齐 Streamlit 设计：新增 Google Trends 区块（开始时间/搜索量排序）与 `↻ RSS` 刷新按钮，展示数据源与刷新时间；新增设置区并提供保存动作。
- [本仓库] FastAPI 新增侧边栏数据接口：`GET /api/sidebar/trends`、`POST /api/sidebar/trends/refresh`、`GET/PUT /api/sidebar/settings`，并挂载 `/assets` 静态目录以提供 `@data/samples/Dummy1.png`。

验证结果:
- 本地接口验证通过：`/api/sidebar/trends`、`/api/sidebar/settings`、`/assets/Dummy1.png` 均可访问并返回预期结果。
- `python -m py_compile src/dashboard_api/server.py` 通过。
- `read_lints` 检查 `src/dashboard_api/server.py` 与 `frontend/board/index.html` 无新增问题。

风险/阻塞:
- 侧边栏设置目前写入 `dashboard_settings_state.json` 的 `default` 会话，尚未接入未来登录体系的用户级隔离。
- 趋势列表目前只显示前 6 条，后续如需完整体验可补分页或滚动容器。

下一步:
- 把设置项（窗口分钟、分类归一化、fallback、fan page）真正连到看板动作请求与读取逻辑，完成“设置即生效”闭环。
- 继续做动作级最小刷新与乐观更新，减少 Live 模式下操作等待感。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板新增三类业务弹窗：`排程`、`修改`、`返回已出未排`，替换原先 `prompt` 粗糙输入；弹窗改为“小时/分钟 + 年/月/日”选择，与 Streamlit 版交互形态对齐。
- [本仓库] 弹窗中的时间输入统一接入“窗口分钟粒度”约束，并在前端按当前时间过滤过去时间槽；更新弹窗同步支持 `link/text/photo/video` 类型、贴文内容与媒体 URL 字段编辑。
- [本仓库] 后端补齐时间窗口规则：`publish` 支持接收前端设置的 `window_minutes`；`update` 新增 `enforce_time_validation + target_action_key + window_minutes` 校验，确保锁定窗口拒绝写入且分钟粒度受控。

验证结果:
- `python -m py_compile src/dashboard_api/server.py src/dashboard_api/services.py src/dashboard_api/schemas.py` 通过。
- `read_lints` 检查本轮改动文件无新增问题。
- 本地页面检查：`/board/` 已包含三类弹窗 DOM；后端动作接口可正常响应（含扩展字段）。

风险/阻塞:
- 当前前端时间过滤基于浏览器本地时区；若后续跨时区使用，需要统一到固定 HKT 显示与计算。
- 删除/修改的确认弹窗目前聚焦 scheduled 场景，后续如重开 published 删除需补“删除贴文”分支文案与字段。

下一步:
- 将弹窗视觉（圆角、按钮位置、文案、辅助说明）进一步精调到与 Streamlit 版更一致。
- 继续推进动作后最小刷新（列级 + 时间段级）与乐观更新回滚策略。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 修复“时间窗口顺延/锁定拒绝”在 Mock 模式下未生效的问题：前端新增 `mockPublishWithRules`，实现与 Live 规则一致的目标窗口锁定拦截、同窗口未锁定贴文链式顺延、并返回影响统计。
- [本仓库] Mock 模式的“修改排程”新增窗口校验（分钟粒度、不能过去、锁定窗口禁止改入），避免测试态与真实态规则偏差。
- [本仓库] 保持 Live 模式规则闭环：`publish` 使用前端设置的 `window_minutes`；`update` 的窗口校验参数继续由后端统一执行。

验证结果:
- `read_lints` 检查 `frontend/board/index.html`、`src/dashboard_api/*` 无新增问题。
- `python -m py_compile src/dashboard_api/server.py src/dashboard_api/services.py src/dashboard_api/schemas.py` 通过。

风险/阻塞:
- 目前 Mock 规则在前端内存实现，仅用于交互验证；真实并发场景仍以后端规则为准。

下一步:
- 增加“顺延影响可视化提示”弹层（列出被顺延文章和目标时段），便于用户确认排程副作用。

日期时间(HKT): 2026-03-30
负责人/LLM: wangz / gpt-5.3-codex
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 按用户反馈补齐“已排程修改时间”场景的完整窗口规则：Mock 修改不再仅做校验后直改，而是执行与排程一致的链式顺延流程（目标窗口锁定拒绝、未锁定冲突后推、遇锁跳过）。
- [本仓库] 修改弹窗确认成功后增加影响反馈文案：显示顺延数量与锁定阻挡次数，便于验证规则生效。

验证结果:
- `read_lints` 检查 `frontend/board/index.html` 无新增问题。

风险/阻塞:
- Mock 顺延规则目前按前端内存状态执行，用于交互验证；最终并发一致性仍依赖后端真实规则。

下一步:
- 继续将“顺延详情（具体哪篇从何时移动到何时）”展示到 UI，提升可解释性。

日期时间(HKT): 2026-04-01
负责人/LLM: wangz / Composer
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 看板「已出未排」七列顺序与产品约定对齐：`CATEGORY_ORDER` 调整为 `社會事/大視野/兩岸/法庭事/消費/娛樂/心韓`（`src/dashboard/config.py`、`frontend/board/index.html`）；Streamlit 横向看板列循环改为统一使用 `CATEGORY_ORDER`（`src/dashboard/board_view.py`）。
- [本仓库] Live 看板读路径修复：`load_board_columns` 在读取样本 JSON 前先调用 `_refresh_live_sample_files`（按 `dashboard_settings_state.json` 的 `cfg_enable_category_alias_mode` / `cfg_target_fan_page_id` 同步），使「立刻刷新 / 定时刷新」与远端 `fb_published` / `fb_scheduled` / `posts` 一致；写动作后的 `_sync_live()` 同样改为读取上述持久化设置，不再硬编码 fan page。
- [本仓库] 看板渲染兜底判定修正：启用兜底时，仅当「已發佈窗口 + 各分类已出未排窗口」均为空才展开全量列表，**不再**因「已排程」列存在未来稿而抑制兜底（避免排程一篇后主列被 24h 窗口滤空、界面只剩已排程）。
- [本仓库] 独立看板动作后刷新策略保持**列级局部拉取**（排程/取消排程仍为 `scheduled + pending:分类`；修改为仅 `scheduled`），以满足效率诉求；全量 `fetchColumns("")` 的临时方案已按反馈撤销。
- [本仓库] Google Trends 侧栏与 Streamlit 对齐：`config.TRENDS_SIDEBAR_DISPLAY_LIMIT = 12`；`GET /api/sidebar/trends` 返回条数上限与 `sidebar_view._render_trends_widget` 一致；Alpine 侧栏热词改为可点击展开卡片，展示开始时间/搜索量及 RSS `detail_items`（最多 3 条链接），并修复原先前端 `slice(0, 6)` 导致条数偏少的问题。

验证结果:
- `python -c` 导入 `get_sidebar_trends` 与 `TRENDS_SIDEBAR_DISPLAY_LIMIT` 通过；返回 `items` 长度不超过 12。
- 代码审阅：`services.py` 兜底条件与 `server.py` trends 截断逻辑与 Streamlit 行为一致。

风险/阻塞:
- 每次 `GET /api/board/columns` 均触发完整 live 同步，RSS/看板刷新频率高时会增加 CMS 与网络负载；若需降载可后续增加可选 `?sync=0` 或服务端节流。
- 关闭「看板渲染兜底」时，已發佈/已出未排仍严格受 24h 窗口与 CMS 时间字段约束，空列属预期行为。

下一步:
- 如需在保持列级刷新的前提下避免「窗口异常时单分类 pending 被写成空」的合并风险，可考虑后端在局部 `include` 响应中附带 `partial_merge_hint` 或前端失败时回退全量拉取（按需启用）。
- 评估看板同步是否与侧边栏 RSS 一样做 TTL/按需刷新，平衡实时性与负载。

日期时间(HKT): 2026-04-02
负责人/LLM: wangz / Composer
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板「API 调用日志」：`apiFetch` 记录浏览器→FastAPI 请求；`live_api_sync.sync_live_data_to_sample_files` 经 `_json_post_traced` 收集远端 CMS 调用链（`login` Basic+JSON、`fb_*`/`posts` Bearer+Cookie），脱敏 headers/密码/token、长 `data` 数组摘要；经 `GET /api/board/columns` 字段 `cms_upstream_calls` 返回（`BoardColumnsResponse` 扩展），前端 `_mergeUpstreamIntoApiLog` 插入同一块可折叠日志，便于对照 `api_smoke_test_app` 行为理解「浏览器只见本地 API、上游在服务端」。
- [本仓库] 「看板渲染兜底」二次修正：此前「已發佈或任一分類已出未排在 24h 内有稿则整表不兜底」会导致其它分类列仍空却像开关失效；改为 **已發佈 / 已排程 分列** 判断，**已出未排按七个分类独立**——仅当该分类在 24h 窗口内无稿时才对该分类使用全量 pending。
- [本仓库] `load_board_columns` 对 pending 排序时间：`publish_time` 解析失败则尝试 `updated_at`，再失败用 epoch，避免整行从时间索引中消失而无法进入兜底全量。
- [本仓库] `live_api_sync._to_pending_rows`：CMS 分类常见 `@栏目` 前缀与 `CATEGORY_ORDER` 不一致导致不进列——增加 `_cms_category_token` 去 `@`；帖子主键兼容 `ID`/`id`。

验证结果:
- `python -m py_compile` 覆盖 `live_api_sync.py`、`services.py`、`schemas.py` 等本轮改动文件通过。
- 设置文件 `cfg_enable_board_fallback_mode` / `cfg_enable_category_alias_mode` 与 FastAPI 读取路径已核对；分类归一化仍在每次 live sync 时生效，需保存设置后刷新看板触发写回样本 JSON。

风险/阻塞:
- `cms_upstream_calls` 随列接口返回，payload 变大；调试日志前端默认最多 80 条。
- 写动作路径（`CmsActionClient`）尚未纳入同一 trace，若需可在后续对 `fb_publish`/`fb_update`/`fb_delete` 做对称埋点。

下一步:
- 按需将 CMS 写操作纳入 `cms_upstream_calls` 或独立 `last_action_trace`。
- 若需减轻负载，可为 `GET /api/board/columns` 增加跳过同步或合并轮询策略。

日期时间(HKT): 2026-04-08
负责人/LLM: wangz / Composer
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板 `frontend/board/index.html`：已發佈 / 已排程 / 已出未排卡片 `publish_time` 不再直接展示 API 存盘的 UTC ISO 字符串；新增 `formatDisplayTimeHkt`，以 `parseToDate` + `Intl.DateTimeFormat(..., timeZone: "Asia/Hong_Kong")` 格式化为 `YYYY-MM-DD HH:mm HKT`，与「修改贴文」弹窗内 HKT 语义一致；「确认删除排程」对话框中「当前排程」同步使用该展示。
- [本仓库] 「返回已出未排」乐观 UI 与「已出未排 → 排程」对齐：先 `closeDialog` 再写入乐观行；新增 `_resolveCategoryColumnKey`（分类须落在 `categoryOrder` 内，否则回退 `娛樂`）；新增 `_ensurePendingCategoryVisible`——侧栏为单分类筛选时，若目标贴文落在另一分类的已出未排，原先 `rebuildColumns` 会把非当前分类列置 `items: []`，导致看不到乐观卡片，故在插入前自动将 `selectedCategory` 切到目标分类；Live 取消排程 API 失败时除 `_restoreRaw` 外恢复此前的 `selectedCategory`。
- [本仓库] Mock `mockDelete`：与 Live 一致为回到 pending 的卡片打上 `_optimistic` / `_optTempId`、清空 `post_link_id`，并先 `closeDialog` 再 `mockDelete` + `_ensurePendingCategoryVisible`。

验证结果:
- 前端为纯展示与状态机调整；侧栏筛选在「全部」与「单分类」下手动点「返回已出未排」可看到灰化乐观卡片出现在对应已出未排列顶部。

风险/阻塞:
- 未知分类名经 `_resolveCategoryColumnKey` 暂统一归入 `娛樂`；若 CMS 出现第七列外新分类，需同步扩展 `categoryOrder` 或映射表。

下一步:
- 视需要为「自动切换侧栏分类」增加轻提示（避免用户误以为筛选被重置）；评估已發佈列时间是否也需统一为「仅日期」等展示策略。

日期时间(HKT): 2026-04-08（续）
负责人/LLM: wangz / Composer
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板侧栏 `frontend/board/index.html`：**数据模式**（Mock / Live API）并入可折叠 **「设置」** 区块，默认 **折叠**；**默认数据模式为 Live API**；移除「开启/停止自动刷新(20s)」及 `setInterval` 轮询，主区仅保留手动 **「刷新全部」**；**折叠侧栏按钮**与标题同排、`margin-left: auto`，右缘与下方 `side-block` 对齐（收起态仍保留窄条上的展开键，`sidebar-head` 置于 `sidebar-content` 外）。
- [本仓库] 与 Streamlit `board_view.py` 对齐的交互与符号：**排程** 📅、**修改** ✏️、**返回已出未排** 🔙；锁定 **🔒 / 🔓**；按钮使用 `title` / `aria-label`（中文）+ `.btn-icon-emoji` 系统 emoji 字体栈，无外链图标依赖，便于 Docker/内网 URL 部署。
- [本仓库] 恢复前两列 **已發佈 / 已排程** 的「隐藏冻结列」能力：`board-shell` 左侧 **📰 / 📅** 控制条（悬停 `data-hint`）、列头可点 **图标 + 标题 + <<<**；`hideColPublished` / `hideColScheduled` 驱动 `.board` 的 `--c1`/`--c2` 与 sticky `left`，隐藏时列宽收束并淡出，行为参照原 Streamlit `toggle-col1/2`。

验证结果:
- 本地 `python -m src.dashboard_api.run` 打开 `/board/` 手测：设置默认折叠、Live 首屏、侧栏折叠对齐、列隐藏与 emoji 按钮可用。

风险/阻塞:
- Emoji 显示仍依赖客户端系统彩色字体；极端环境若显示方框，用户可依赖 `title` / `aria-label`。

下一步:
- 若需与 Streamlit 完全一致，锁定可改回内联 SVG（当前为 Unicode 锁形 emoji）。

日期时间(HKT): 2026-04-13
负责人/LLM: wangz / GPT-5.4
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 独立看板 `frontend/board/index.html` 的「修改贴文」弹窗与「设置排程时间」弹窗对齐：补齐 `post_message` 文本框、`Add URL`、`link/text/photo` 类型切换、photo 预览与图片 URL、HKT `日/月/年` 日期选择及对应状态逻辑；`confirmUpdate()` 改为与当前三种类型约束一致，`photo` 强校验图片，`post_mp4_url` 统一传空串。
- [本仓库] `src/dashboard/live_api_sync.py` 修正已排程/已发布类型识别：新增对 CMS `fb_scheduled`/`fb_published` 返回 `type: "text"` 的映射，不再把 text 误落成 link；同时补强 CMS 文章映射，优先用文章 URL `link` 回填 CMS post，并增加 `category_by_cms_id` 以在 `fb_scheduled` 未直接返回栏目时回填真实分类，减少 `scheduled.category = 未分類`。
- [本仓库] 已排程展示窗口从 `24h` 放宽为 `7 天`：`src/dashboard/config.py` 新增 `BOARD_SCHEDULED_LOOKAHEAD_DAYS`，并同步到 `src/dashboard_api/services.py` 与 `src/dashboard/board_view.py`，避免隔天凌晨/未来数日的排程因为窗口过短在看板中“看不见”。
- [本仓库] 「返回已出未排」删除链路修正：前端新增分类别名归一化（如 `心韩 -> 心韓`、`娱乐 -> 娛樂`）；删除时若当前 scheduled 卡片分类未知/为 `未分類`，不再错误乐观插入 `娛樂` 列，而是仅从已排程移除，并在 API 完成后刷新 `scheduled,pending`；若分类已知则继续局部刷新 `scheduled,pending:<分类>`。

验证结果:
- 已手动验证：`心韓` 与 `消費` 分类的「返回已出未排」乐观 UI 会先出现在正确列位。
- 本地静态检查通过：`python -m py_compile src/dashboard/live_api_sync.py` 无语法错误；`frontend/board/index.html` 仅保留既有 CSS `line-clamp` 兼容性 warning。

风险/阻塞:
- `GET /api/board/columns?include=...` 当前虽然支持局部返回，但后端 `load_board_columns()` 仍会先触发一次完整 `_refresh_live_sample_files()`，因此删除/局部刷新时仍会串行调用 `fb_published`、`fb_scheduled` 与全部分类 `posts`，耗时偏长；下一步需拆分“上游全量同步”和“局部列返回”。
- `api_smoke_test_app.py` 侧目前仍存在“修改已排程贴文类型”不生效/不便测试的问题，尚未在本轮修复。
- 若 CMS `fb_scheduled` / `fb_published` 既不给分类，又无法通过 `link -> CMS post` 反查成功，scheduled 行仍可能保留 `未分類`；当前删除链路已兜底为刷新全部 pending，但彻底修复仍依赖上游返回更稳定的文章关联信息。

下一步:
- 为 `/api/board/columns` 增加“跳过实时全量同步”或“按 include 仅刷新必要上游接口”的模式，缩短删除/修改后的局部刷新耗时。
- 继续排查并修复 `api_smoke_test_app.py` 中已排程贴文类型修改能力，使 Smoke Test 与 FastAPI 看板行为一致。

日期时间(HKT): 2026-04-13（续）
负责人/LLM: wangz / GPT-5.4
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 更新 `docs/governance/TECHSTACK.MD`：补充当前主用 FastAPI 看板 UI 技术栈说明，明确区分前端 `HTML/CSS/JavaScript + Alpine.js`、后端 `FastAPI`，以及 `uvicorn` 仅作为 ASGI server / 启动方式；同步记录 `/board` 与 `/assets` 为 `StaticFiles` 挂载、Live 模式依赖 `src/dashboard.live_api_sync` 改写样本文件。
- [本仓库] 优化 `GET /api/board/columns` 局部刷新链路：`src/dashboard_api/services.py` 的 `load_board_columns()` 新增 `sync_live` 开关，`src/dashboard_api/server.py` 暴露 `sync` 查询参数；动作成功后的前端二次回读（排程 / 修改 / 删除 / 锁定）统一通过 `frontend/board/index.html` 传 `sync=false`，改为直接读取刚同步好的样本文件，不再重复触发一整轮 `fb_published`、`fb_scheduled` 与全部分类 `posts`。
- [本仓库] 更新看板前端 API 日志标识：`fetchColumns()` 在 `skipSync` 场景下将日志类型标为 `GET board/columns（局部，无同步）` / `GET board/columns（全量，无同步）`，便于肉眼区分“读取本地样本”和“实时拉取 CMS”的请求。

验证结果:
- 本地静态检查通过：`python -m py_compile src/dashboard_api/server.py src/dashboard_api/services.py` 无语法错误。
- 代码层面确认：手动「刷新全部」仍走默认 `sync=true`；动作成功后的局部 UI 回读改走 `sync=false`，避免重复全量同步。

风险/阻塞:
- 当前动作接口 `publish_from_pending()` / `update_scheduled()` / `delete_scheduled()` 内部仍会在成功后调用 `_sync_live()`，因此虽然去掉了“动作后再读 columns 时重复同步”的第二轮开销，但动作本身仍是一次全量 CMS 刷新；若还需继续提速，需要进一步拆分动作后的最小必要同步。
- `api_smoke_test_app.py` 中“修改已排程贴文类型”的问题仍未修复，需后续单独排查。

下一步:
- 继续拆解动作接口内部的 `_sync_live()`，评估按动作类型最小化刷新（例如仅重建 `scheduled` + 受影响分类 pending）的可行性。
- 在线验证 API 日志是否已从“动作后两轮全量 CMS 请求”收敛为“动作内一轮同步 + 局部无同步回读”。

日期时间(HKT): 2026-04-13（续二）
负责人/LLM: wangz / GPT-5.4
分支/worktree: feature/bot-ui-ops（本仓库）
完成内容:
- [本仓库] 调整独立看板侧栏「栏目筛选」作用域：`frontend/board/index.html` 中 `rebuildColumns()` 仅对 **已發佈**、**已排程** 两列按 `selectedCategory` 过滤；**已出未排** 七列始终完整展示，不再因单选筛选被置空。侧栏副标题改为「栏目筛选（仅已发布 / 已排程）」以免误解。
- [本仓库] 移除 `_ensurePendingCategoryVisible` 及删除流程中对 `selectedCategory` 的自动切换与失败回滚（此前为在筛选非目标列时仍能看到 pending 乐观卡片）；在「筛选只影响前两列」后不再需要该行为。

验证结果:
- 逻辑自检：`rebuildColumns` 中 pending 分支不再依赖 `selectedCategory`；`confirmDelete` mock/live 路径已无 `_ensurePendingCategoryVisible` 调用。

风险/阻塞:
- 若 `published` / `scheduled` 行 `category` 仍为 `未分類` 或与侧栏键不一致，筛选后该列可能为空；依赖后端 `live_api_sync` 分类回填与别名归一化（前端 `_normalizeCategoryKey`）尽量对齐。

下一步:
- 视产品需要，可为「仅前两列筛选」增加空态提示（例如「当前栏目下暂无已排程」）。
