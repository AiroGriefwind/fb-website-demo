# Scheduler plugin (FB engine on CMS board)

## What was added

- Python package `src/scheduler_plugin/`: ported auto-scheduler (calendar slots, `SchedulerEngine`, traffic mock, HK holidays) from the legacy FB-scheduler repo, without SQLite.
- FastAPI routes on the dashboard app:
  - `POST /api/scheduler/generate` — optional CMS sync, reads `data/samples/dashboard_pending.json` (+ optional published for repost pool), returns suggested rows.
  - `POST /api/scheduler/apply` — body `{ "items": [ { "item_id", "schedule_time", "immediate_publish", "window_minutes", ... } ], "stop_on_error": true }` — each row calls existing `publish_from_pending` (CMS + sync).
- `src/dashboard_api/services.py`: `sync_live_board_samples()` and `apply_scheduler_batch()`.
- Board UI (`frontend/board/index.html`): bulk scheduler modal adds **引擎全自動建議**; **確認送出** in Live mode calls `/api/scheduler/apply` (Mock mode still only logs to console).

## When to use `sync=true`

- `GET /api/board/columns?sync=true` (default) and `POST /api/scheduler/generate` with `"sync": true` both pull CMS and rewrite sample JSON under `data/samples/`.
- For rapid UI refresh after you know data is fresh, use `sync=false` on board columns (already supported) and `"sync": false` on generate to avoid duplicate upstream calls.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `FAKE_NOW` | ISO datetime for reproducible engine “now” (HKT). |
| `SCHEDULER_ENABLE_REPOST_JOB` | Set to `1` / `true` / `yes` / `on` to register APScheduler cron at **23:50 HKT** calling `SchedulerEngine.run_2350_repost_job` (delegates to JSON-based `repost_nightly.run_nightly_repost_job`, no DB writes). |

## How to run the app

From repo root (with dependencies installed):

```bash
python -m src.dashboard_api.run
```

This starts `uvicorn` on `src.dashboard_api.server:app` and serves `/board/`.

## Tests

```bash
pip install -r requirements.txt
pytest tests/test_scheduler_plugin.py
```

Run from repository root so `src` resolves on `PYTHONPATH` (pytest collects from `tests/`).

## Notes

- Category mapping: board **娛樂** maps to engine **娛圈事**; unknown CMS buckets (e.g. `SourceR`) map to **社會事** for slot matching.
- `apply` uses real CMS credentials via existing `CmsActionClient`; failures return HTTP 400 with the first error message when `stop_on_error` is true.
