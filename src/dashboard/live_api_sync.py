from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import parse, request

import streamlit as st
from dotenv import dotenv_values

from src.dashboard.config import CATEGORY_ORDER, HKT_TZ, PENDING_FILE, PUBLISHED_FILE, SCHEDULED_FILE
from src.dashboard_api.cms_client import _extract_token as _cms_extract_token

ENV_PATH = Path(__file__).resolve().parents[2] / "configs" / ".env"
ENV_VALUES = {k: v for k, v in dotenv_values(ENV_PATH).items() if isinstance(v, str)}
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEBUG_LOG_PATH = WORKSPACE_ROOT / "debug-8a72c3.log"
DEBUG_SESSION_ID = "8a72c3"
DEBUG_RUN_ID = f"run-{int(time.time() * 1000)}"
CATEGORY_ALIASES = {
    "娛圈事": "娛樂",
    "娱乐": "娛樂",
    "娛樂": "娛樂",
    "社會": "社會事",
    "社会事": "社會事",
    "社會事": "社會事",
    "大视野": "大視野",
    "大視野": "大視野",
    "两岸": "兩岸",
    "兩岸": "兩岸",
    "法庭": "法庭事",
    "法庭事": "法庭事",
    "消费": "消費",
    "消費": "消費",
    "心韩": "心韓",
    "心 韓": "心韓",
    "心韓": "心韓",
}


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    entry = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": DEBUG_RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _header_shape(headers: dict[str, str]) -> dict[str, Any]:
    auth_value = headers.get("Authorization", "")
    return {
        "has_authorization": "Authorization" in headers,
        "authorization_prefix": auth_value.split(" ", 1)[0] if auth_value else "",
        "has_cookie": "Cookie" in headers,
        "has_cookies": "Cookies" in headers,
        "has_x_token": "X-Token" in headers,
        "content_type": headers.get("Content-Type", ""),
    }


def _secret_or_env(key: str, default: str = "") -> str:
    value = ""
    try:
        secrets = st.secrets
        if key in secrets:
            raw = secrets.get(key, "")
            value = str(raw or "").strip()
    except Exception:
        value = ""
    if value:
        return value
    env_value = os.getenv(key, "").strip()
    if env_value:
        return env_value
    file_value = str(ENV_VALUES.get(key, "")).strip()
    if file_value:
        return file_value
    return default


def _extract_basic_from_url(url: str) -> tuple[str, str, str]:
    parsed = parse.urlsplit(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url, "", ""
    username = parse.unquote(parsed.username or "")
    password = parse.unquote(parsed.password or "")
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    sanitized = parse.urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    return sanitized, username, password


def _normalize_endpoint_url(raw_base_url: str) -> str:
    base = raw_base_url.strip()
    if not base:
        return ""
    base = base.rstrip("/")
    if base.endswith("/index.php"):
        return base
    if base.endswith("/fb-scheduler"):
        return f"{base}/"
    return f"{base}/fb-scheduler/"


def _trace_time_label() -> str:
    d = datetime.now(HKT_TZ)
    return d.strftime("%H:%M:%S.") + f"{d.microsecond // 1000:03d}"


def _trace_safe_headers(headers: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = str(k).lower()
        if lk == "authorization":
            if str(v).startswith("Bearer "):
                out[k] = "Bearer ***"
            elif str(v).startswith("Basic "):
                out[k] = "Basic ***"
            else:
                out[k] = "***"
        elif lk in ("cookie", "cookies"):
            s = str(v)
            out[k] = (s[:20] + "…") if len(s) > 20 else (s or "")
        elif lk == "x-token":
            out[k] = "***"
        else:
            out[k] = str(v)
    return out


def _trace_safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    p = {k: v for k, v in payload.items() if v is not None}
    if "password" in p:
        p = dict(p)
        p["password"] = "***"
    return p


def _compact_trace_response(data: Any) -> Any:
    """Shrink large CMS JSON for UI trace; redact tokens in nested data dict."""
    if not isinstance(data, dict):
        return data
    out = dict(data)
    inner = out.get("data")
    if isinstance(inner, dict):
        di = dict(inner)
        for tk in ("token", "access_token"):
            if di.get(tk):
                di[tk] = "***"
        out["data"] = di
    elif isinstance(inner, list):
        n = len(inner)
        if n > 3:
            sample: list[Any] = []
            for it in inner[:2]:
                if isinstance(it, dict):
                    keys = ("title", "message", "keyword", "id", "post_title", "ID")
                    slim = {k: it.get(k) for k in keys if k in it}
                    if not slim:
                        slim = {"_keys": list(it.keys())[:12]}
                    sample.append(slim)
                else:
                    sample.append(str(it)[:120])
            out["data"] = sample
            out["_trace_note"] = f"data 数组共 {n} 条，此处仅预览前 2 条摘要"
        else:
            out["data"] = inner
    return out


def _json_post_traced(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    trace: list[dict[str, Any]],
    call_label: str,
) -> tuple[int, dict[str, str], Any]:
    t0 = time.perf_counter()
    time_label = _trace_time_label()
    safe_req = {"json": _trace_safe_payload(payload), "headers": _trace_safe_headers(headers)}
    try:
        code, hdrs, data = _json_post(url, payload, headers)
    except Exception as exc:
        dur = int((time.perf_counter() - t0) * 1000)
        trace.append(
            {
                "kind": call_label,
                "layer": "upstream_cms",
                "timeLabel": time_label,
                "method": "POST",
                "url": url,
                "status": None,
                "ok": False,
                "durationMs": dur,
                "requestBody": safe_req,
                "responseBody": None,
                "error": str(exc),
            }
        )
        raise
    dur = int((time.perf_counter() - t0) * 1000)
    trace.append(
        {
            "kind": call_label,
            "layer": "upstream_cms",
            "timeLabel": time_label,
            "method": "POST",
            "url": url,
            "status": int(code),
            "ok": 200 <= int(code) < 400,
            "durationMs": dur,
            "requestBody": safe_req,
            "responseBody": _compact_trace_response(data),
        }
    )
    return code, hdrs, data


def _json_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> tuple[int, dict[str, str], Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    # region agent log
    _debug_log(
        hypothesis_id="H6-H7",
        location="live_api_sync.py:_json_post",
        message="Sending JSON request",
        data={
            "url": url,
            "action": str(payload.get("action", "")),
            "header_shape": _header_shape(headers),
        },
    )
    # endregion
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw_text": text}
        # region agent log
        _debug_log(
            hypothesis_id="H6-H7-H8",
            location="live_api_sync.py:_json_post",
            message="Received JSON response",
            data={
                "status_code": resp.getcode(),
                "action": str(payload.get("action", "")),
                "response_has_set_cookie": bool(resp.headers.get("Set-Cookie")),
            },
        )
        # endregion
        return resp.getcode(), dict(resp.headers), data


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_category(raw: str, enable_alias_mode: bool) -> str:
    key = str(raw or "").strip().replace(" ", "")
    if not key:
        return "未分類"
    if enable_alias_mode:
        return CATEGORY_ALIASES.get(key, key)
    return key


def _safe_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def _derive_post_link_id(item: dict[str, Any]) -> str:
    direct = str(item.get("post_link_id", "")).strip()
    if direct:
        return direct
    raw_id = str(item.get("id", "")).strip()
    if "_" in raw_id:
        return raw_id
    post_url = str(item.get("permalink_url", "")).strip() or str(item.get("link", "")).strip()
    marker = "/posts/"
    if marker in post_url:
        return post_url.split(marker, 1)[1].split("?", 1)[0].strip().strip("/")
    if "permalink.php" in post_url:
        try:
            parsed = parse.urlsplit(post_url)
            query = parse.parse_qs(parsed.query)
            page_id = str((query.get("id") or [""])[0]).strip()
            story_fbid = str((query.get("story_fbid") or [""])[0]).strip()
            if page_id and story_fbid:
                return f"{page_id}_{story_fbid}"
        except Exception:
            return ""
    return ""


def _derive_post_id(item: dict[str, Any]) -> int:
    direct = _safe_int(item.get("post_id"))
    if direct > 0:
        return direct
    raw_id = str(item.get("id", "")).strip()
    if "_" in raw_id:
        parent = _safe_int(raw_id.split("_", 1)[0].strip())
        if parent > 0:
            return parent
    permalink = str(item.get("permalink_url", "")).strip()
    marker = "facebook.com/"
    if marker in permalink:
        path = permalink.split(marker, 1)[1]
        head = path.split("/", 1)[0]
        head_id = _safe_int(head)
        if head_id > 0:
            return head_id
    if "permalink.php" in permalink:
        try:
            parsed = parse.urlsplit(permalink)
            query = parse.parse_qs(parsed.query)
            page_id = _safe_int((query.get("id") or [""])[0])
            if page_id > 0:
                return page_id
        except Exception:
            return 0
    return 0


def _normalize_post_type(raw: str) -> str:
    normalized = str(raw or "").strip().lower()
    if normalized in {"link", "text", "photo", "video"}:
        return normalized
    return "link"


def _post_link_type_from_fb_item(item: dict[str, Any]) -> str:
    """Graph API 常用 `type`（如 status=纯文字），与 CMS `post_link_type` 并存；仅后者时勿默认成 link。"""
    direct = str(item.get("post_link_type", "")).strip()
    if direct:
        return _normalize_post_type(direct)
    fb_t = str(item.get("type", "")).strip().lower()
    # Graph 常见 status；CMS fb_scheduled 也可能直接返回 type=text
    if fb_t in {"status", "native_templates", "text"}:
        return "text"
    if fb_t in {"link", "photo", "video"}:
        return fb_t
    if fb_t == "share":
        return "link"
    return "link"


def _build_cms_reference_maps(
    posts_items: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, int], dict[int, str], dict[int, str]]:
    by_post_link_id: dict[str, int] = {}
    by_post_link: dict[str, int] = {}
    thumb_by_cms_id: dict[int, str] = {}
    category_by_cms_id: dict[int, str] = {}
    for item in posts_items:
        cms_id = _safe_int(item.get("ID"))
        if cms_id <= 0:
            continue
        post_link = str(item.get("post_link", "")).strip()
        if post_link:
            by_post_link[post_link] = cms_id
        categories = item.get("categories", [])
        if isinstance(categories, list) and categories:
            raw_cat = str(categories[0] or "").strip().replace(" ", "")
        else:
            raw_cat = str(item.get("category", "") or "").strip().replace(" ", "")
        if raw_cat.startswith("@"):
            raw_cat = raw_cat[1:]
        cms_cat = _normalize_category(raw_cat, enable_alias_mode=True)
        if cms_cat != "未分類":
            category_by_cms_id[cms_id] = cms_cat
        cms_thumb = (
            str(item.get("feature_image", "")).strip()
            or str(item.get("image_url", "")).strip()
            or str(item.get("post_thumbnail", "")).strip()
        )
        fan_pages = item.get("fan_pages", [])
        if isinstance(fan_pages, list):
            for row in fan_pages:
                if not isinstance(row, dict):
                    continue
                link_id = str(row.get("post_link_id", "")).strip()
                if link_id:
                    by_post_link_id[link_id] = cms_id
                if not cms_thumb:
                    cms_thumb = (
                        str(row.get("image_url", "")).strip()
                        or str(row.get("thumbnail", "")).strip()
                        or str(row.get("feature_image", "")).strip()
                    )
        if cms_thumb:
            thumb_by_cms_id[cms_id] = cms_thumb
    return by_post_link_id, by_post_link, thumb_by_cms_id, category_by_cms_id


def _extract_fan_page_entry(item: dict[str, Any], target_fan_page_id: str) -> dict[str, Any]:
    fan_pages = item.get("fan_pages", [])
    if not isinstance(fan_pages, list):
        return {}
    target = str(target_fan_page_id or "").strip()
    for row in fan_pages:
        if not isinstance(row, dict):
            continue
        current_id = str(row.get("id", "")).strip()
        if target and current_id == target:
            return row
    return {}


def _is_already_scheduled_by_fan_page(item: dict[str, Any], target_fan_page_id: str) -> bool:
    fan = _extract_fan_page_entry(item, target_fan_page_id)
    if not fan:
        return False
    link = str(fan.get("link", "")).strip()
    post_link_id = str(fan.get("post_link_id", "")).strip()
    return bool(link and post_link_id)


def _build_scheduled_thumb_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in rows:
        key = str(row.get("post_link_id", "")).strip()
        thumb = str(row.get("thumbnail", "")).strip() or str(row.get("image_url", "")).strip()
        if key and thumb:
            mapping[key] = thumb
    return mapping


def _build_pending_thumb_maps(rows: list[dict[str, Any]]) -> tuple[dict[int, str], dict[str, str]]:
    by_post_id: dict[int, str] = {}
    by_title: dict[str, str] = {}
    for row in rows:
        thumb = str(row.get("thumbnail", "")).strip() or str(row.get("image_url", "")).strip()
        if not thumb:
            continue
        post_id = _safe_int(row.get("post_id"))
        if post_id > 0:
            by_post_id[post_id] = thumb
        title = str(row.get("title", "")).strip()
        if title:
            by_title[title] = thumb
    return by_post_id, by_title


def _to_published_rows(
    items: list[dict[str, Any]],
    enable_alias_mode: bool,
    cms_id_by_post_link_id: dict[str, int] | None = None,
    cms_id_by_post_link: dict[str, int] | None = None,
    thumb_by_cms_id: dict[int, str] | None = None,
    pending_thumb_by_post_id: dict[int, str] | None = None,
    pending_thumb_by_title: dict[str, str] | None = None,
    category_by_cms_id: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cms_id_by_post_link_id = cms_id_by_post_link_id or {}
    cms_id_by_post_link = cms_id_by_post_link or {}
    thumb_by_cms_id = thumb_by_cms_id or {}
    pending_thumb_by_post_id = pending_thumb_by_post_id or {}
    pending_thumb_by_title = pending_thumb_by_title or {}
    category_by_cms_id = category_by_cms_id or {}
    for item in items:
        insights = item.get("insights", {}) if isinstance(item.get("insights", {}), dict) else {}
        title = str(item.get("message", "")).strip() or str(item.get("id", "Untitled")).strip() or "Untitled"
        post_link_id = _derive_post_link_id(item)
        permalink = str(item.get("permalink_url", "")).strip()
        article_link = str(item.get("link", "")).strip()
        post_link = permalink or article_link
        cms_post_id = cms_id_by_post_link_id.get(post_link_id, 0) if post_link_id else 0
        if cms_post_id <= 0:
            for candidate in (article_link, permalink):
                if candidate:
                    cms_post_id = cms_id_by_post_link.get(candidate, 0)
                if cms_post_id > 0:
                    break
        if cms_post_id <= 0:
            cms_post_id = _derive_post_id(item)
        category = _normalize_category(str(item.get("category", "未分類")), enable_alias_mode)
        if category == "未分類" and cms_post_id > 0:
            category = str(category_by_cms_id.get(cms_post_id, category)).strip() or category
        # Keep image recovery chain consistent with scheduled/pending columns:
        # 1) fb payload full_picture/image_url
        # 2) cms reference map by cms_id
        # 3) pending-derived map by cms post_id
        # 4) pending-derived map by title
        current_thumb = str(item.get("full_picture", "")).strip() or str(item.get("image_url", "")).strip()
        if not current_thumb and cms_post_id > 0:
            current_thumb = str(thumb_by_cms_id.get(cms_post_id, "")).strip()
        if not current_thumb and cms_post_id > 0:
            current_thumb = str(pending_thumb_by_post_id.get(cms_post_id, "")).strip()
        if not current_thumb:
            current_thumb = str(pending_thumb_by_title.get(title, "")).strip()
        rows.append(
            {
                "title": title,
                "category": category,
                "thumbnail": current_thumb,
                "Post URL": post_link,
                "publish_time": str(item.get("created_time", "")).strip(),
                "popular_count": int(insights.get("post_impressions_unique") or 0),
                "post_id": cms_post_id,
                "item_id": str(cms_post_id) if cms_post_id > 0 else "",
                "post_link_id": post_link_id,
                "post_link_type": _post_link_type_from_fb_item(item),
                "post_message": str(item.get("message", "")).strip(),
                "image_url": str(item.get("image_url", "")).strip() or current_thumb,
                "post_mp4_url": str(item.get("post_mp4_url", "")).strip(),
                "raw_fb_id": str(item.get("id", "")).strip(),
            }
        )
    return rows


def _to_scheduled_rows(
    items: list[dict[str, Any]],
    enable_alias_mode: bool,
    thumb_fallback_map: dict[str, str] | None = None,
    cms_id_by_post_link_id: dict[str, int] | None = None,
    cms_id_by_post_link: dict[str, int] | None = None,
    thumb_by_cms_id: dict[int, str] | None = None,
    category_by_cms_id: dict[int, str] | None = None,
    pending_thumb_by_post_id: dict[int, str] | None = None,
    pending_thumb_by_title: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    thumb_fallback_map = thumb_fallback_map or {}
    cms_id_by_post_link_id = cms_id_by_post_link_id or {}
    cms_id_by_post_link = cms_id_by_post_link or {}
    thumb_by_cms_id = thumb_by_cms_id or {}
    category_by_cms_id = category_by_cms_id or {}
    pending_thumb_by_post_id = pending_thumb_by_post_id or {}
    pending_thumb_by_title = pending_thumb_by_title or {}
    for item in items:
        title = str(item.get("message", "")).strip() or str(item.get("id", "Untitled")).strip() or "Untitled"
        current_link_id = _derive_post_link_id(item)
        current_thumb = str(item.get("full_picture", "")).strip() or str(item.get("image_url", "")).strip()
        if not current_thumb and current_link_id:
            current_thumb = str(thumb_fallback_map.get(current_link_id, "")).strip()
        permalink = str(item.get("permalink_url", "")).strip()
        article_link = str(item.get("link", "")).strip()
        current_link = permalink or article_link
        cms_post_id = cms_id_by_post_link_id.get(current_link_id, 0) if current_link_id else 0
        if cms_post_id <= 0:
            for candidate in (article_link, permalink):
                if candidate:
                    cms_post_id = cms_id_by_post_link.get(candidate, 0)
                if cms_post_id > 0:
                    break
        if cms_post_id <= 0:
            cms_post_id = _derive_post_id(item)
        if not current_thumb and cms_post_id > 0:
            current_thumb = str(thumb_by_cms_id.get(cms_post_id, "")).strip()
        if not current_thumb and cms_post_id > 0:
            current_thumb = str(pending_thumb_by_post_id.get(cms_post_id, "")).strip()
        if not current_thumb:
            current_thumb = str(pending_thumb_by_title.get(title, "")).strip()
        category = _normalize_category(str(item.get("category", "未分類")), enable_alias_mode)
        if category == "未分類" and cms_post_id > 0:
            category = str(category_by_cms_id.get(cms_post_id, category)).strip() or category
        rows.append(
            {
                "title": title,
                "category": category,
                "thumbnail": current_thumb,
                "Post URL": current_link,
                "publish_time": str(item.get("scheduled_publish_time", "")).strip()
                or str(item.get("created_time", "")).strip(),
                "popular_count": 0,
                "post_id": cms_post_id,
                "item_id": str(cms_post_id) if cms_post_id > 0 else "",
                "post_link_id": current_link_id,
                "post_link_type": _post_link_type_from_fb_item(item),
                "post_message": str(item.get("message", "")).strip(),
                "image_url": str(item.get("image_url", "")).strip() or current_thumb,
                "post_mp4_url": str(item.get("post_mp4_url", "")).strip(),
                "raw_fb_id": str(item.get("id", "")).strip(),
            }
        )
    return rows


def _cms_category_token(raw: str) -> str:
    """CMS 常返回「@消費」等带 @ 前缀的分类，与看板 CATEGORY_ORDER 不一致时会被整列丢弃。"""
    s = str(raw or "").strip().replace(" ", "")
    if s.startswith("@"):
        s = s[1:]
    return s


def _to_pending_rows(
    items: list[dict[str, Any]],
    now_iso: str,
    enable_alias_mode: bool,
    target_fan_page_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        post_id = str(item.get("ID") or item.get("id") or "").strip()
        if not post_id:
            continue
        if _is_already_scheduled_by_fan_page(item, target_fan_page_id):
            continue
        fan_page_entry = _extract_fan_page_entry(item, target_fan_page_id)
        categories = item.get("categories", [])
        if isinstance(categories, list) and categories:
            cat = _cms_category_token(str(categories[0]))
        else:
            cat = _cms_category_token(str(item.get("category", "")))
        cat = _normalize_category(cat, enable_alias_mode)
        rows.append(
            {
                "item_id": post_id,
                "run_id": f"api-sync-{datetime.now(HKT_TZ).strftime('%Y%m%d')}",
                "category": cat,
                "title": str(item.get("post_title", "")).strip() or f"Post {post_id}",
                "thumbnail": str(item.get("feature_image", "")).strip(),
                "Post URL": str(item.get("post_link", "")).strip(),
                "publish_time": str(item.get("post_date_gmt", "")).strip().replace(" ", "T") + "Z",
                "popular_count": 0,
                "review_status": "waiting",
                "updated_at": now_iso,
                "post_id": _safe_int(post_id),
                "post_link_id": str(fan_page_entry.get("post_link_id", "")).strip(),
                "post_link_type": _normalize_post_type(
                    str(fan_page_entry.get("post_link_type", "")).strip() or str(item.get("post_link_type", "link")).strip()
                ),
                "post_message": str(fan_page_entry.get("post_message", "")).strip()
                or str(item.get("post_message", "")).strip()
                or str(item.get("post_title", "")).strip(),
                "image_url": str(fan_page_entry.get("image_url", "")).strip()
                or str(item.get("image_url", "")).strip()
                or str(item.get("feature_image", "")).strip(),
                "post_mp4_url": str(item.get("post_mp4_url", "")).strip(),
                "target_fan_page_id": target_fan_page_id,
            }
        )
    return rows


def read_cms_use_production_from_settings() -> bool:
    """与看板「设置」中 CMS 环境开关一致（dashboard_settings_state.json）。"""
    settings_file = WORKSPACE_ROOT / "data" / "samples" / "dashboard_settings_state.json"
    try:
        raw = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}
        sessions = raw.get("sessions", {}) if isinstance(raw.get("sessions", {}), dict) else {}
        default = sessions.get("default", {}) if isinstance(sessions.get("default", {}), dict) else {}
        v = str(default.get("cfg_cms_environment", default.get("cms_environment", "staging"))).strip().lower()
        return v in ("production", "prod")
    except Exception:
        return False


def _extract_data_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        data = payload.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


@st.cache_data(show_spinner=False, ttl=60)
def sync_live_data_to_sample_files(
    enable_category_alias_mode: bool = False,
    target_fan_page_id: str = "",
    use_production: bool = False,
) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    try:
        use_prod = bool(use_production)
        # region agent log
        _debug_log(
            hypothesis_id="H6",
            location="live_api_sync.py:sync_live_data_to_sample_files",
            message="Sync function entered",
            data={
                "enable_category_alias_mode": bool(enable_category_alias_mode),
                "use_production": use_prod,
            },
        )
        # endregion
        if use_prod:
            api_base = _secret_or_env("PRODUCTION_API_BASE_URL")
            basic_user = _secret_or_env("PRODUCTION_BASIC_AUTH_USERNAME")
            basic_pass = _secret_or_env("PRODUCTION_BASIC_AUTH_PASSWORD")
        else:
            api_base = _secret_or_env("API_BASE_URL")
            basic_user = _secret_or_env("BASIC_AUTH_USERNAME")
            basic_pass = _secret_or_env("BASIC_AUTH_PASSWORD")
        username = _secret_or_env("USERNAME")
        password = _secret_or_env("PASSWORD")
        posts_limit = int(_secret_or_env("API_POSTS_LIMIT", "10") or 10)

        if not api_base or not username or not password:
            miss = "PRODUCTION_API_BASE_URL/USERNAME/PASSWORD" if use_prod else "API_BASE_URL/USERNAME/PASSWORD"
            return {"ok": False, "message": f"missing {miss}", "cms_upstream_calls": trace}

        api_url, url_user, url_pass = _extract_basic_from_url(api_base)
        api_url = _normalize_endpoint_url(api_url)
        basic_user = basic_user or url_user
        basic_pass = basic_pass or url_pass

        login_headers = {"Content-Type": "application/json; charset=utf-8"}
        if basic_user or basic_pass:
            raw = f"{basic_user}:{basic_pass}".encode("utf-8")
            login_headers["Authorization"] = f"Basic {base64.b64encode(raw).decode('ascii')}"

        code, login_resp_headers, login_payload = _json_post_traced(
            api_url,
            {"action": "login", "username": username, "password": password},
            login_headers,
            trace=trace,
            call_label="CMS login（Basic 网关 + JSON 用户名密码 → token）",
        )
        token = _cms_extract_token(login_payload) if isinstance(login_payload, dict) else ""
        if code != 200 or not token:
            # region agent log
            _debug_log(
                hypothesis_id="H7-H8",
                location="live_api_sync.py:sync_live_data_to_sample_files",
                message="Login failed for sync flow",
                data={"status_code": code, "token_present": bool(token)},
            )
            # endregion
            return {
                "ok": False,
                "message": f"login failed ({code})",
                "login_payload": login_payload,
                "cms_upstream_calls": trace,
            }

        session_cookie = str(login_resp_headers.get("Set-Cookie", "")).split(";", 1)[0].strip()
        if use_prod:
            common_headers = {"Content-Type": "application/json; charset=utf-8"}
            if basic_user or basic_pass:
                raw_b = f"{basic_user}:{basic_pass}".encode("utf-8")
                common_headers["Authorization"] = f"Basic {base64.b64encode(raw_b).decode('ascii')}"
            common_headers["X-Token"] = token
            if session_cookie:
                common_headers["Cookies"] = session_cookie
            pub_label = "CMS fb_published（Basic + X-Token + Cookies）"
            sch_label = "CMS fb_scheduled（Basic + X-Token + Cookies）"
            posts_suffix = "Basic + X-Token + Cookies）"
        else:
            common_headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            }
            if session_cookie:
                common_headers["Cookie"] = session_cookie
            pub_label = "CMS fb_published（Bearer + Cookie）"
            sch_label = "CMS fb_scheduled（Bearer + Cookie）"
            posts_suffix = "Bearer + Cookie）"

        _, _, published_payload = _json_post_traced(
            api_url,
            {"action": "fb_published"},
            common_headers,
            trace=trace,
            call_label=pub_label,
        )
        _, _, scheduled_payload = _json_post_traced(
            api_url,
            {"action": "fb_scheduled"},
            common_headers,
            trace=trace,
            call_label=sch_label,
        )

        now_iso = datetime.now(HKT_TZ).isoformat()
        fan_page_id = str(target_fan_page_id or _secret_or_env("TARGET_FAN_PAGE_ID", "350584865140118")).strip()
        pending_rows_all: list[dict[str, Any]] = []
        seen_pending: set[str] = set()
        posts_items_all: list[dict[str, Any]] = []
        for cat in CATEGORY_ORDER:
            _, _, posts_payload = _json_post_traced(
                api_url,
                {"action": "posts", "category": cat, "search": "", "limit": posts_limit},
                common_headers,
                trace=trace,
                call_label=f"CMS posts（{cat}，{posts_suffix}",
            )
            current_posts_items = _extract_data_list(posts_payload)
            posts_items_all.extend(current_posts_items)
            for row in _to_pending_rows(
                current_posts_items,
                now_iso,
                enable_alias_mode=enable_category_alias_mode,
                target_fan_page_id=fan_page_id,
            ):
                item_id = str(row.get("item_id", "")).strip()
                if item_id and item_id not in seen_pending:
                    seen_pending.add(item_id)
                    pending_rows_all.append(row)

        cms_id_by_post_link_id, cms_id_by_post_link, thumb_by_cms_id, category_by_cms_id = _build_cms_reference_maps(
            posts_items_all
        )
        pending_thumb_by_post_id, pending_thumb_by_title = _build_pending_thumb_maps(pending_rows_all)
        published_rows = _to_published_rows(
            _extract_data_list(published_payload),
            enable_alias_mode=enable_category_alias_mode,
            cms_id_by_post_link_id=cms_id_by_post_link_id,
            cms_id_by_post_link=cms_id_by_post_link,
            thumb_by_cms_id=thumb_by_cms_id,
            pending_thumb_by_post_id=pending_thumb_by_post_id,
            pending_thumb_by_title=pending_thumb_by_title,
            category_by_cms_id=category_by_cms_id,
        )
        scheduled_thumb_fallback_map = _build_scheduled_thumb_map(pending_rows_all)
        scheduled_rows = _to_scheduled_rows(
            _extract_data_list(scheduled_payload),
            enable_alias_mode=enable_category_alias_mode,
            thumb_fallback_map=scheduled_thumb_fallback_map,
            cms_id_by_post_link_id=cms_id_by_post_link_id,
            cms_id_by_post_link=cms_id_by_post_link,
            thumb_by_cms_id=thumb_by_cms_id,
            category_by_cms_id=category_by_cms_id,
            pending_thumb_by_post_id=pending_thumb_by_post_id,
            pending_thumb_by_title=pending_thumb_by_title,
        )

        _write_rows(PUBLISHED_FILE, published_rows)
        _write_rows(SCHEDULED_FILE, scheduled_rows)
        _write_rows(PENDING_FILE, pending_rows_all)

        return {
            "ok": True,
            "published_count": len(published_rows),
            "scheduled_count": len(scheduled_rows),
            "pending_count": len(pending_rows_all),
            "source_url": api_url,
            "target_fan_page_id": fan_page_id,
            "cms_upstream_calls": trace,
        }
    except Exception as exc:  # noqa: BLE001 - keep dashboard alive on sync failure.
        # region agent log
        _debug_log(
            hypothesis_id="H8",
            location="live_api_sync.py:sync_live_data_to_sample_files",
            message="Sync function raised exception",
            data={"exception_type": type(exc).__name__, "has_message": bool(str(exc))},
        )
        # endregion
        return {"ok": False, "message": str(exc), "cms_upstream_calls": trace}
