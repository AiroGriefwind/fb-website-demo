from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.dashboard.config import (
    DEFAULT_SCHEDULE_WINDOW_MINUTES,
    HKT_TZ,
    PENDING_FILE,
    PUBLISHED_FILE,
    SCHEDULED_FILE,
    SAMPLES_DIR,
    TRENDS_SIDEBAR_DISPLAY_LIMIT,
    TRENDS_WEB_URL,
)
from src.dashboard.data_utils import (
    load_trending_keywords,
    load_trending_keywords_from_rss,
    persist_trending_keywords,
    published_to_sort_ts,
    read_json_list,
    traffic_to_int,
)
from src.dashboard_api.schemas import (
    BoardColumnsResponse,
    DeleteRequest,
    PublishRequest,
    SchedulerApplyRequest,
    SchedulerGenerateRequest,
    ToggleLockRequest,
    UpdateRequest,
)
from src.dashboard_api.services import (
    apply_scheduler_batch,
    delete_all_published,
    delete_scheduled,
    load_board_columns,
    publish_from_pending,
    sync_live_board_samples,
    toggle_lock,
    update_scheduled,
)


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    scheduler = None
    flag = os.getenv("SCHEDULER_ENABLE_REPOST_JOB", "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        from apscheduler.schedulers.background import BackgroundScheduler

        from src.scheduler_plugin.services.scheduler_engine import SchedulerEngine

        scheduler = BackgroundScheduler(timezone="Asia/Hong_Kong")
        scheduler.add_job(SchedulerEngine().run_2350_repost_job, "cron", hour=23, minute=50)
        scheduler.start()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Dashboard API", version="0.1.0", lifespan=_app_lifespan)

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
LEGACY_SCHEDULER_ROOT = Path(
    os.getenv(
        "LEGACY_SCHEDULER_REPO",
        str(WORKSPACE_ROOT / "frontend" / "legacy_scheduler"),
    )
)
LEGACY_CONSOLE_FILE = LEGACY_SCHEDULER_ROOT / "templates" / "console.html"
LEGACY_WIDGET_FILE = LEGACY_SCHEDULER_ROOT / "static" / "bastille-widget.js"

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


def _load_legacy_console_html() -> str:
    if not LEGACY_CONSOLE_FILE.exists():
        return f"<h1>Legacy console file not found: {LEGACY_CONSOLE_FILE}</h1>"
    html = LEGACY_CONSOLE_FILE.read_text(encoding="utf-8")
    html = html.replace(
        'const BASE_URL = "http://127.0.0.1:8000";',
        "const BASE_URL = window.location.origin;",
    )
    # 原始版本 confirmSchedule 存在 response/res 变量名不一致，这里只修该处。
    html = html.replace('const response = await fetch("/schedule/confirm", {', 'const res = await fetch("/schedule/confirm", {')
    html = html.replace("const data = await response.json();", "const data = await res.json();")
    html = html.replace(
        'is_immediate: row.querySelector(".immediate").checked',
        'is_immediate: row.querySelector(".immediate").checked,\n                article_id: row.querySelector(".articleId").value',
    )
    html = html.replace(
        '    if (data.post_type) row.querySelector(".postType").value = data.post_type;',
        '    if (data.post_type) row.querySelector(".postType").value = data.post_type;\n'
        '    if (data.article_id) row.querySelector(".articleId").value = String(data.article_id);',
    )
    html = html.replace("if (data.schedule) {", "if (Array.isArray(data.schedule)) {")
    html = html.replace(
        "        scheduleGenerated = true;",
        "        scheduleGenerated = data.schedule.length > 0;",
    )
    html = html.replace(
        '            alert("❌ 送出失敗");',
        '            alert("❌ 送出失敗: " + (data.message || "unknown"));',
    )
    # 插入“加载中/状态提示”条，增强可感知性和排错能力。
    status_ui = """
<div id="legacyStatusBar" style="position:fixed;left:12px;right:12px;bottom:10px;z-index:10000;background:#0f172a;color:#e2e8f0;padding:8px 10px;border-radius:8px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.18);display:none;">
  <span id="legacyStatusText">Ready</span>
</div>
<script>
(function(){
  function setLegacyStatus(text, keepMs){
    const bar = document.getElementById("legacyStatusBar");
    const txt = document.getElementById("legacyStatusText");
    if(!bar || !txt) return;
    txt.textContent = text || "";
    bar.style.display = text ? "block" : "none";
    if (keepMs && keepMs > 0) {
      window.clearTimeout(window.__legacyStatusTimer);
      window.__legacyStatusTimer = window.setTimeout(()=>{ bar.style.display = "none"; }, keepMs);
    }
  }
  window.setLegacyStatus = setLegacyStatus;

  const _gen = window.generateEntertainment;
  if (typeof _gen === "function") {
    window.generateEntertainment = async function(){
      setLegacyStatus("正在生成排程建議…", 0);
      try {
        await _gen.apply(this, arguments);
        const n = document.querySelectorAll("#scheduleTable tbody tr").length;
        if (n > 0) setLegacyStatus("排程建議已載入 " + n + " 條", 3500);
        else setLegacyStatus("已完成，但沒有可顯示的建議（可先檢查分類/資料來源）", 5000);
      } catch (e) {
        setLegacyStatus("生成失敗：" + (e && e.message ? e.message : e), 7000);
        throw e;
      }
    };
  }

  const _repost = window.generateRepostOnly;
  if (typeof _repost === "function") {
    window.generateRepostOnly = async function(){
      setLegacyStatus("正在生成 Repost 建議…", 0);
      try {
        await _repost.apply(this, arguments);
        const n = document.querySelectorAll("#scheduleTable tbody tr").length;
        setLegacyStatus("Repost 操作完成，當前表格 " + n + " 條", 3500);
      } catch (e) {
        setLegacyStatus("Repost 失敗：" + (e && e.message ? e.message : e), 7000);
        throw e;
      }
    };
  }

  const _search = window.searchArticles;
  if (typeof _search === "function") {
    window.searchArticles = async function(inputElement){
      const kw = (inputElement && inputElement.value || "").trim();
      if (kw.length >= 2) setLegacyStatus("正在搜尋「" + kw + "」…", 0);
      try {
        await _search.apply(this, arguments);
        setLegacyStatus("搜尋完成", 1200);
      } catch (e) {
        setLegacyStatus("搜尋失敗：" + (e && e.message ? e.message : e), 5000);
        throw e;
      }
    };
  }

  const _latest = window.loadLatest;
  if (typeof _latest === "function") {
    window.loadLatest = async function(button){
      setLegacyStatus("正在載入可選文章…", 0);
      try {
        await _latest.apply(this, arguments);
        setLegacyStatus("可選文章已更新", 1500);
      } catch (e) {
        setLegacyStatus("載入失敗：" + (e && e.message ? e.message : e), 5000);
        throw e;
      }
    };
  }

  const _confirm = window.confirmSchedule;
  if (typeof _confirm === "function") {
    window.confirmSchedule = async function(event){
      setLegacyStatus("正在送出排程…", 0);
      try {
        await _confirm.apply(this, arguments);
        setLegacyStatus("送出完成", 2000);
      } catch (e) {
        setLegacyStatus("送出失敗：" + (e && e.message ? e.message : e), 7000);
        throw e;
      }
    };
  }
})();
</script>
"""
    html = html.replace("</body>", status_ui + "\n</body>")
    return html


def _load_legacy_widget_js() -> str:
    if not LEGACY_WIDGET_FILE.exists():
        return f"console.error('Legacy widget file not found: {LEGACY_WIDGET_FILE.as_posix()}');"
    js = LEGACY_WIDGET_FILE.read_text(encoding="utf-8")
    js = js.replace(
        'const BASE_URL = "http://127.0.0.1:8000";',
        "const BASE_URL = window.location.origin;",
    )
    return js


def _normalize_console_category(raw: str) -> str:
    category = str(raw or "").strip()
    alias = {
        "娛圈事": "娛樂",
        "娱乐": "娛樂",
        "社會": "社會事",
        "社会事": "社會事",
        "两岸": "兩岸",
        "大视野": "大視野",
        "法庭": "法庭事",
        "Repost": "娛樂",
    }
    return alias.get(category, category or "社會事")


def _collect_legacy_article_rows() -> list[dict[str, Any]]:
    rows = [
        *read_json_list(PENDING_FILE),
        *read_json_list(SCHEDULED_FILE),
        *read_json_list(PUBLISHED_FILE),
    ]
    dedup: dict[str, dict[str, Any]] = {}
    for r in rows:
        key = str(r.get("item_id", "") or r.get("post_id", "") or "").strip()
        if not key:
            key = str(r.get("title", "")).strip()
        if not key:
            continue
        dedup[key] = r
    return list(dedup.values())


def _item_id_from_console_row(row: dict[str, Any], pending_rows: list[dict[str, Any]]) -> str:
    raw_article_id = str(row.get("article_id", "") or "").strip()
    if raw_article_id:
        return raw_article_id
    title = str(row.get("title", "") or "").strip()
    if not title:
        return ""
    category = _normalize_console_category(str(row.get("category", "")))
    exact = next(
        (
            r
            for r in pending_rows
            if str(r.get("title", "")).strip() == title
            and _normalize_console_category(str(r.get("category", ""))) == category
        ),
        None,
    )
    if exact:
        return str(exact.get("item_id", "") or exact.get("post_id", "") or "").strip()
    fuzzy = next((r for r in pending_rows if str(r.get("title", "")).strip() == title), None)
    if fuzzy:
        return str(fuzzy.get("item_id", "") or fuzzy.get("post_id", "") or "").strip()
    return ""


@app.get("/console", response_class=HTMLResponse)
def legacy_console_page() -> str:
    return _load_legacy_console_html()


@app.get("/scheduler-widget.js", response_class=PlainTextResponse)
def legacy_scheduler_widget_js() -> PlainTextResponse:
    return PlainTextResponse(_load_legacy_widget_js(), media_type="application/javascript")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "module": "dashboard_api"}


@app.get("/alerts/pending")
def legacy_pending_alert() -> dict[str, Any]:
    # 兼容同事 UI 结构：status + alert
    return {"status": "success", "alert": None}


@app.get("/articles/latest")
def legacy_latest_articles(category: str | None = Query(default=None)) -> dict[str, Any]:
    rows = _collect_legacy_article_rows()
    cat = _normalize_console_category(category or "")
    if category:
        filtered = [r for r in rows if _normalize_console_category(str(r.get("category", ""))) == cat]
        rows = filtered if filtered else rows
    return {
        "results": [
            {
                "id": str(r.get("item_id", "") or r.get("post_id", "") or ""),
                "title": str(r.get("title", "")),
            }
            for r in rows[:30]
        ]
    }


@app.get("/articles/search")
def legacy_search_articles(
    q: str = Query(default=""),
    category: str | None = Query(default=None),
) -> dict[str, Any]:
    keyword = q.strip().lower()
    rows = _collect_legacy_article_rows()
    if category:
        cat = _normalize_console_category(category)
        filtered = [r for r in rows if _normalize_console_category(str(r.get("category", ""))) == cat]
        rows = filtered if filtered else rows
    if keyword:
        rows = [r for r in rows if keyword in str(r.get("title", "")).lower()]
    return {
        "results": [
            {
                "id": str(r.get("item_id", "") or r.get("post_id", "") or ""),
                "title": str(r.get("title", "")),
            }
            for r in rows[:30]
        ]
    }


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
    try:
        _eg = int(current.get("cfg_early_publish_guard_slots", current.get("early_publish_guard_slots", 2)) or 2)
    except Exception:
        _eg = 2
    _eg = max(1, min(5, _eg))
    _cms_env = str(current.get("cfg_cms_environment", current.get("cms_environment", "staging"))).strip() or "staging"
    if _cms_env.lower() in ("production", "prod"):
        _cms_env = "production"
    else:
        _cms_env = "staging"
    return {
        "schedule_window_minutes": int(current.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "early_publish_guard_slots": _eg,
        "enable_category_alias_mode": bool(current.get("cfg_enable_category_alias_mode", False)),
        "enable_board_fallback_mode": bool(current.get("cfg_enable_board_fallback_mode", False)),
        "use_fake_link": bool(current.get("cfg_use_fake_link", current.get("use_fake_link", False))),
        "fake_link_url": str(current.get("cfg_fake_link_url", current.get("fake_link_url", "https://abc.xyz/test-link"))).strip()
        or "https://abc.xyz/test-link",
        "target_fan_page_id": str(current.get("cfg_target_fan_page_id", "350584865140118")).strip() or "350584865140118",
        "cms_environment": _cms_env,
        "updated_at": str(current.get("updated_at", "")),
    }


@app.put("/api/sidebar/settings")
def put_sidebar_settings(payload: dict[str, Any]) -> dict[str, Any]:
    raw = _load_settings_state()
    sessions = raw.get("sessions", {}) if isinstance(raw.get("sessions", {}), dict) else {}
    try:
        _eg_put = int(payload.get("early_publish_guard_slots", 2) or 2)
    except Exception:
        _eg_put = 2
    _eg_put = max(1, min(5, _eg_put))
    _cms_in = str(payload.get("cms_environment", "staging") or "staging").strip().lower()
    _cms_norm = "production" if _cms_in in ("production", "prod") else "staging"
    sessions["default"] = {
        "cfg_schedule_window_minutes": int(payload.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "schedule_window_minutes": int(payload.get("schedule_window_minutes", DEFAULT_SCHEDULE_WINDOW_MINUTES)),
        "cfg_early_publish_guard_slots": _eg_put,
        "early_publish_guard_slots": _eg_put,
        "cfg_enable_category_alias_mode": bool(payload.get("enable_category_alias_mode", False)),
        "cfg_enable_board_fallback_mode": bool(payload.get("enable_board_fallback_mode", False)),
        "cfg_use_fake_link": bool(payload.get("use_fake_link", False)),
        "use_fake_link": bool(payload.get("use_fake_link", False)),
        "cfg_fake_link_url": str(payload.get("fake_link_url", "https://abc.xyz/test-link")).strip()
        or "https://abc.xyz/test-link",
        "fake_link_url": str(payload.get("fake_link_url", "https://abc.xyz/test-link")).strip()
        or "https://abc.xyz/test-link",
        "cfg_target_fan_page_id": str(payload.get("target_fan_page_id", "350584865140118")).strip() or "350584865140118",
        "cfg_cms_environment": _cms_norm,
        "cms_environment": _cms_norm,
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
    sync: bool = Query(
        default=True,
        description="Whether to sync live CMS data before reading board sample files.",
    ),
) -> dict:
    includes = [x.strip() for x in (include or "").split(",") if x.strip()]
    return load_board_columns(includes=includes or None, sync_live=bool(sync))


@app.post("/api/actions/publish")
def action_publish(payload: PublishRequest) -> dict:
    result = publish_from_pending(
        item_id=payload.item_id,
        schedule_time=payload.schedule_time,
        window_minutes=int(payload.window_minutes or DEFAULT_SCHEDULE_WINDOW_MINUTES),
        post_message=str(payload.post_message or ""),
        post_link_type=str(payload.post_link_type or "link"),
        image_url=str(payload.image_url or ""),
        immediate_publish=bool(payload.immediate_publish),
        allow_shift=bool(payload.allow_shift),
        schedule_method=str(payload.schedule_method or "manual_user"),
    )
    if not bool(result.get("ok")):
        if bool(result.get("requires_confirmation")):
            raise HTTPException(status_code=409, detail=result)
        raise HTTPException(status_code=400, detail=str(result.get("message", "publish failed")))
    return result


@app.post("/api/actions/update")
def action_update(payload: UpdateRequest) -> dict:
    result = update_scheduled(payload.model_dump())
    if not bool(result.get("ok")):
        if bool(result.get("requires_confirmation")):
            raise HTTPException(status_code=409, detail=result)
        raise HTTPException(status_code=400, detail=str(result.get("message", "update failed")))
    return result


@app.post("/api/actions/delete")
def action_delete(payload: DeleteRequest) -> dict:
    result = delete_scheduled(post_id=payload.post_id, post_link_id=payload.post_link_id)
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "delete failed")))
    return result


@app.post("/api/actions/delete-published-all")
def action_delete_published_all() -> dict:
    result = delete_all_published()
    if not bool(result.get("ok")) and int(result.get("deleted", 0) or 0) == 0:
        raise HTTPException(status_code=400, detail=str(result.get("message", "bulk delete published failed")))
    return result


@app.post("/api/actions/toggle-lock")
def action_toggle_lock(payload: ToggleLockRequest) -> dict:
    result = toggle_lock(action_key=payload.action_key)
    if not bool(result.get("ok")):
        raise HTTPException(status_code=400, detail=str(result.get("message", "toggle lock failed")))
    return result


@app.post("/api/scheduler/generate")
def scheduler_generate(payload: SchedulerGenerateRequest) -> dict[str, Any]:
    if bool(payload.sync):
        sync_live_board_samples()
    pending_rows = read_json_list(PENDING_FILE)
    published_rows = read_json_list(PUBLISHED_FILE) if payload.include_published_for_repost else None
    from src.scheduler_plugin.pipeline import generate_schedule_suggestions

    out = generate_schedule_suggestions(
        pending_rows=pending_rows,
        published_rows=published_rows,
        schedule_date=payload.schedule_date.strip(),
        include_published_for_repost=bool(payload.include_published_for_repost),
        repost_engagement_threshold=float(payload.repost_engagement_threshold),
    )
    if not bool(out.get("ok")):
        raise HTTPException(status_code=400, detail=str(out.get("message", "generate failed")))
    return out


@app.post("/schedule/generate")
def legacy_schedule_generate(payload: dict[str, Any]) -> dict[str, Any]:
    schedule_date = str(payload.get("schedule_date", "") or "").strip()
    if not schedule_date:
        schedule_date = datetime.now(HKT_TZ).strftime("%Y-%m-%d")
    out = scheduler_generate(
        SchedulerGenerateRequest(
            schedule_date=schedule_date,
            sync=True,
            include_published_for_repost=True,
            repost_engagement_threshold=50.0,
        )
    )
    schedule = [
        {
            "title": row.get("title", ""),
            "category": row.get("engine_category", "") or row.get("category_display", ""),
            "time": row.get("schedule_time", ""),
            "suggested_post_type": row.get("suggested_post_type", "link_post"),
            "article_id": row.get("item_id", ""),
        }
        for row in out.get("schedule", [])
    ]
    return {
        "status": "success",
        "batch_id": f"legacy-{int(datetime.now().timestamp())}",
        "generated_at": out.get("generated_at", ""),
        "schedule": schedule,
    }


@app.post("/repost/generate")
def legacy_repost_generate() -> dict[str, Any]:
    published = read_json_list(PUBLISHED_FILE)
    target_date = datetime.now(HKT_TZ).date().strftime("%Y-%m-%d")
    slots = ["01:30", "02:30", "03:30", "04:30", "05:30", "06:30"]
    candidates = sorted(
        published,
        key=lambda r: float(r.get("popular_count") or r.get("views") or 0),
        reverse=True,
    )
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(candidates[: len(slots)]):
        out.append(
            {
                "title": str(row.get("title", "")),
                "time": f"{target_date}T{slots[idx]}",
                "suggested_post_type": "link_post",
            }
        )
    return {"status": "success", "target_date": target_date, "count": len(out), "schedule": out}


@app.post("/schedule/confirm")
def legacy_schedule_confirm(payload: dict[str, Any]) -> dict[str, Any]:
    posts = payload.get("posts", [])
    if not isinstance(posts, list) or not posts:
        return {"status": "error", "message": "posts required"}
    pending_rows = read_json_list(PENDING_FILE)
    apply_items: list[dict[str, Any]] = []
    for row in posts:
        if not isinstance(row, dict):
            continue
        item_id = _item_id_from_console_row(row, pending_rows)
        if not item_id:
            title = str(row.get("title", "")).strip() or "N/A"
            return {"status": "error", "message": f"unable to map row to item_id: {title}"}
        post_type = str(row.get("post_type", "link_post")).strip().lower()
        post_link_type = (
            "video" if "video" in post_type else
            "photo" if "photo" in post_type else
            "text" if "text" in post_type else
            "link"
        )
        apply_items.append(
            {
                "item_id": item_id,
                "schedule_time": str(row.get("scheduled_time", "") or ""),
                "immediate_publish": bool(row.get("is_immediate", False)),
                "window_minutes": int(DEFAULT_SCHEDULE_WINDOW_MINUTES),
                "post_message": str(row.get("title", "") or ""),
                "post_link_type": post_link_type,
                "image_url": "",
                "allow_shift": True,
                "schedule_method": "auto_plugin",
            }
        )
    result = apply_scheduler_batch(apply_items, stop_on_error=False)
    rows = result.get("results", []) if isinstance(result.get("results"), list) else []
    ok_rows = [r for r in rows if bool(r.get("ok"))]
    failed_rows = [r for r in rows if not bool(r.get("ok"))]
    if failed_rows:
        first_msg = str(failed_rows[0].get("message", "unknown error"))
        return {
            "status": "error",
            "message": f"部分送出失敗：成功 {len(ok_rows)} / 失敗 {len(failed_rows)}，首個錯誤：{first_msg}",
            "count": len(ok_rows),
            "failed": len(failed_rows),
        }
    return {
        "status": "success",
        "message": f"Schedule confirmed: {len(ok_rows)} rows",
        "count": len(ok_rows),
        "failed": 0,
    }


@app.post("/api/scheduler/apply")
def scheduler_apply(payload: SchedulerApplyRequest) -> dict[str, Any]:
    items = [it.model_dump() for it in payload.items]
    if not items:
        raise HTTPException(status_code=400, detail="items required")
    result = apply_scheduler_batch(items, stop_on_error=bool(payload.stop_on_error))
    if not bool(result.get("ok")):
        raise HTTPException(
            status_code=400,
            detail=str(result.get("message", "apply failed")),
        )
    return result

