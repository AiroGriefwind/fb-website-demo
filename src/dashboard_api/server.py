from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.dashboard.config import (
    DEFAULT_SCHEDULE_WINDOW_MINUTES,
    HKT_TZ,
    SAMPLES_DIR,
    TRENDS_SIDEBAR_DISPLAY_LIMIT,
    TRENDS_WEB_URL,
)
from src.dashboard.data_utils import (
    load_trending_keywords,
    load_trending_keywords_from_rss,
    persist_trending_keywords,
    published_to_sort_ts,
    traffic_to_int,
)
from src.dashboard_api.schemas import (
    BoardColumnsResponse,
    DeleteRequest,
    PublishRequest,
    ToggleLockRequest,
    UpdateRequest,
)
from src.dashboard_api.services import (
    delete_scheduled,
    load_board_columns,
    publish_from_pending,
    toggle_lock,
    update_scheduled,
)

app = FastAPI(title="Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = WORKSPACE_ROOT / "frontend" / "board"
SETTINGS_STATE_FILE = SAMPLES_DIR / "dashboard_settings_state.json"

if FRONTEND_DIR.exists():
    app.mount("/board", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="board")
if SAMPLES_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(SAMPLES_DIR), html=False), name="assets")


def _load_settings_state() -> dict[str, Any]:
    if not SETTINGS_STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(SETTINGS_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _save_settings_state(payload: dict[str, Any]) -> None:
    SETTINGS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/board/")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "module": "dashboard_api"}


@app.get("/api/sidebar/trends")
def get_sidebar_trends(sort: str = Query(default="time", pattern="^(time|volume)$")) -> dict[str, Any]:
    trends = load_trending_keywords()
    using_rss = any(str(item.get("source", "")).lower() == "rss" for item in trends)
    if sort == "time":
        trends = sorted(trends, key=published_to_sort_ts, reverse=True)
    else:
        trends = sorted(trends, key=lambda x: traffic_to_int(str(x.get("search_volume", ""))), reverse=True)
    return {
        "items": trends[:TRENDS_SIDEBAR_DISPLAY_LIMIT],
        "source": "rss" if using_rss else "sample",
        "source_url": TRENDS_WEB_URL,
        "refreshed_at": datetime.now(HKT_TZ).strftime("%m-%d %H:%M"),
    }


@app.post("/api/sidebar/trends/refresh")
def refresh_sidebar_trends() -> dict[str, Any]:
    load_trending_keywords_from_rss.clear()
    latest = load_trending_keywords_from_rss()
    if latest:
        persist_trending_keywords(latest)
    return {"ok": bool(latest), "count": len(latest), "message": "rss refreshed" if latest else "rss unavailable"}


@app.get("/api/sidebar/settings")
def get_sidebar_settings() -> dict[str, Any]:
    raw = _load_settings_state()
    sessions = raw.get("sessions", {}) if isinstance(raw.get("sessions", {}), dict) else {}
    current = sessions.get("default", {})
    if not isinstance(current, dict):
        current = {}
    return {
        "schedule_window_minutes": int(current.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "enable_category_alias_mode": bool(current.get("cfg_enable_category_alias_mode", False)),
        "enable_board_fallback_mode": bool(current.get("cfg_enable_board_fallback_mode", False)),
        "target_fan_page_id": str(current.get("cfg_target_fan_page_id", "350584865140118")).strip() or "350584865140118",
        "updated_at": str(current.get("updated_at", "")),
    }


@app.put("/api/sidebar/settings")
def put_sidebar_settings(payload: dict[str, Any]) -> dict[str, Any]:
    raw = _load_settings_state()
    sessions = raw.get("sessions", {}) if isinstance(raw.get("sessions", {}), dict) else {}
    sessions["default"] = {
        "cfg_schedule_window_minutes": int(payload.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "schedule_window_minutes": int(payload.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "cfg_enable_category_alias_mode": bool(payload.get("enable_category_alias_mode", False)),
        "cfg_enable_board_fallback_mode": bool(payload.get("enable_board_fallback_mode", False)),
        "cfg_target_fan_page_id": str(payload.get("target_fan_page_id", "350584865140118")).strip() or "350584865140118",
        "updated_at": datetime.now(HKT_TZ).isoformat(),
    }
    raw["sessions"] = sessions
    _save_settings_state(raw)
    return {"ok": True, "message": "settings saved"}


@app.get("/api/board/columns", response_model=BoardColumnsResponse)
def get_board_columns(
    include: str | None = Query(
        default=None,
        description="Comma-separated columns, e.g. scheduled,pending:娛樂 or published,scheduled,pending",
    ),
) -> dict:
    includes = [x.strip() for x in (include or "").split(",") if x.strip()]
    return load_board_columns(includes=includes or None)


@app.post("/api/actions/publish")
def action_publish(payload: PublishRequest) -> dict:
    result = publish_from_pending(
        item_id=payload.item_id,
        schedule_time=payload.schedule_time,
        window_minutes=int(payload.window_minutes or DEFAULT_SCHEDULE_WINDOW_MINUTES),
    )
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "publish failed")))
    return result


@app.post("/api/actions/update")
def action_update(payload: UpdateRequest) -> dict:
    result = update_scheduled(payload.model_dump())
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "update failed")))
    return result


@app.post("/api/actions/delete")
def action_delete(payload: DeleteRequest) -> dict:
    result = delete_scheduled(post_id=payload.post_id, post_link_id=payload.post_link_id)
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "delete failed")))
    return result


@app.post("/api/actions/toggle-lock")
def action_toggle_lock(payload: ToggleLockRequest) -> dict:
    result = toggle_lock(action_key=payload.action_key)
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "toggle lock failed")))
    return result

