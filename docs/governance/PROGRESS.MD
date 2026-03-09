# PROGRESS

## 使用规则
- 每次推进后追加一条，不覆盖历史。
- 记录必须包含：时间、分支/worktree、完成项、验证、风险、下一步。

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