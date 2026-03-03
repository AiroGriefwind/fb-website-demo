# STRUCTURE

## 目标目录结构
```text
BP CMS Scraper/
├─ artifacts/
│  ├─ screenshots/
│  └─ html_dumps/
├─ configs/
│  ├─ secrets/
│  └─ serviceAccountKey.example.json
├─ data/
│  ├─ samples/
│  └─ runtime/
├─ docs/
│  ├─ governance/
│  ├─ runbooks/
│  └─ architecture/
├─ scripts/
│  ├─ cron/
│  ├─ deploy/
│  └─ maintenance/
├─ src/
│  ├─ scraper/
│  ├─ scoring/
│  ├─ scheduler/
│  ├─ bot/
│  ├─ dashboard/
│  └─ common/
├─ cms_scraper.py           # 兼容入口（调用 src.scraper）
├─ firebase_utils.py        # 兼容入口（调用 src.common）
└─ requirements.txt
```

## 文件落位规范
- `src/`：业务代码与模块。
- `scripts/`：部署、升级、定时任务脚本。
- `data/samples/`：脱敏样本数据（可入库）。
- `data/runtime/`：运行时数据快照（默认不入库）。
- `artifacts/`：截图、HTML dump、失败现场。
- `configs/`：模板配置文件，不提交真实密钥。

## 本仓库立即迁移规则
- 根目录 `*.png` -> `artifacts/screenshots/`
- 根目录 `login_fail_*.html` -> `artifacts/html_dumps/`
- 根目录 `fb_*json` -> `data/samples/`
- `cms_scraper.py` 迁移到 `src/scraper/cms_scraper.py`，根目录保留兼容入口。
- `firebase_utils.py` 迁移到 `src/common/firebase_utils.py`，根目录保留兼容入口。

## Git 提交规则
- 禁止提交真实密钥（如 `serviceAccountKey.json`）。
- 尽量避免提交运行时噪音文件（截图、临时 json、html dump）。
- 每个功能分支只改对应目录，减少冲突。

