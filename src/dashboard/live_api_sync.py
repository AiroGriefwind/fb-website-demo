from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request

import streamlit as st
from dotenv import dotenv_values

from src.dashboard.config import CATEGORY_ORDER, HKT_TZ, PENDING_FILE, PUBLISHED_FILE, SCHEDULED_FILE

ENV_PATH = Path(__file__).resolve().parents[2] / "configs" / ".env"
ENV_VALUES = {k: v for k, v in dotenv_values(ENV_PATH).items() if isinstance(v, str)}
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


def _safe_json_decode(raw_text: str) -> Any:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw_text": raw_text}


def _json_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body_json = {k: v for k, v in payload.items() if v is not None}
    body_raw = json.dumps(body_json, ensure_ascii=False)
    body = body_raw.encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    req_payload = {
        "method": "POST",
        "url": url,
        "headers": headers,
        "body_json": body_json,
        "body_raw": body_raw,
    }
    try:
        with request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status_code": resp.getcode(),
                "request": req_payload,
                "response_headers": dict(resp.headers),
                "response_json": _safe_json_decode(text),
            }
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status_code": int(exc.code or 0),
            "request": req_payload,
            "response_headers": dict(exc.headers),
            "response_json": _safe_json_decode(text),
            "error": f"HTTPError: {exc.reason}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status_code": 0,
            "request": req_payload,
            "response_headers": {},
            "response_json": {},
            "error": str(exc),
        }


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


def _build_cms_reference_maps(posts_items: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    by_post_link_id: dict[str, int] = {}
    by_post_link: dict[str, int] = {}
    for item in posts_items:
        cms_id = _safe_int(item.get("ID"))
        if cms_id <= 0:
            continue
        post_link = str(item.get("post_link", "")).strip()
        if post_link:
            by_post_link[post_link] = cms_id
        fan_pages = item.get("fan_pages", [])
        if isinstance(fan_pages, list):
            for row in fan_pages:
                if not isinstance(row, dict):
                    continue
                link_id = str(row.get("post_link_id", "")).strip()
                if link_id:
                    by_post_link_id[link_id] = cms_id
    return by_post_link_id, by_post_link


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


def _to_published_rows(
    items: list[dict[str, Any]],
    enable_alias_mode: bool,
    cms_id_by_post_link_id: dict[str, int] | None = None,
    cms_id_by_post_link: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cms_id_by_post_link_id = cms_id_by_post_link_id or {}
    cms_id_by_post_link = cms_id_by_post_link or {}
    for item in items:
        insights = item.get("insights", {}) if isinstance(item.get("insights", {}), dict) else {}
        title = str(item.get("message", "")).strip() or str(item.get("id", "Untitled")).strip() or "Untitled"
        post_link_id = _derive_post_link_id(item)
        post_link = str(item.get("permalink_url", "")).strip() or str(item.get("link", "")).strip()
        cms_post_id = cms_id_by_post_link_id.get(post_link_id, 0) if post_link_id else 0
        if cms_post_id <= 0 and post_link:
            cms_post_id = cms_id_by_post_link.get(post_link, 0)
        if cms_post_id <= 0:
            cms_post_id = _derive_post_id(item)
        rows.append(
            {
                "title": title,
                "category": _normalize_category(str(item.get("category", "未分類")), enable_alias_mode),
                "thumbnail": str(item.get("full_picture", "")).strip(),
                "Post URL": post_link,
                "publish_time": str(item.get("created_time", "")).strip(),
                "popular_count": int(insights.get("post_impressions_unique") or 0),
                "post_id": cms_post_id,
                "item_id": str(cms_post_id) if cms_post_id > 0 else "",
                "post_link_id": post_link_id,
                "post_link_type": _normalize_post_type(str(item.get("post_link_type", "")).strip()),
                "post_message": str(item.get("message", "")).strip(),
                "image_url": str(item.get("image_url", "")).strip()
                or str(item.get("full_picture", "")).strip(),
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
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    thumb_fallback_map = thumb_fallback_map or {}
    cms_id_by_post_link_id = cms_id_by_post_link_id or {}
    cms_id_by_post_link = cms_id_by_post_link or {}
    for item in items:
        title = str(item.get("message", "")).strip() or str(item.get("id", "Untitled")).strip() or "Untitled"
        current_link_id = _derive_post_link_id(item)
        current_thumb = str(item.get("full_picture", "")).strip() or str(item.get("image_url", "")).strip()
        if not current_thumb and current_link_id:
            current_thumb = str(thumb_fallback_map.get(current_link_id, "")).strip()
        current_link = str(item.get("permalink_url", "")).strip() or str(item.get("link", "")).strip()
        cms_post_id = cms_id_by_post_link_id.get(current_link_id, 0) if current_link_id else 0
        if cms_post_id <= 0 and current_link:
            cms_post_id = cms_id_by_post_link.get(current_link, 0)
        if cms_post_id <= 0:
            cms_post_id = _derive_post_id(item)
        rows.append(
            {
                "title": title,
                "category": _normalize_category(str(item.get("category", "未分類")), enable_alias_mode),
                "thumbnail": current_thumb,
                "Post URL": current_link,
                "publish_time": str(item.get("scheduled_publish_time", "")).strip()
                or str(item.get("created_time", "")).strip(),
                "popular_count": 0,
                "post_id": cms_post_id,
                "item_id": str(cms_post_id) if cms_post_id > 0 else "",
                "post_link_id": current_link_id,
                "post_link_type": _normalize_post_type(str(item.get("post_link_type", "")).strip()),
                "post_message": str(item.get("message", "")).strip(),
                "image_url": str(item.get("image_url", "")).strip() or current_thumb,
                "post_mp4_url": str(item.get("post_mp4_url", "")).strip(),
                "raw_fb_id": str(item.get("id", "")).strip(),
            }
        )
    return rows


def _to_pending_rows(
    items: list[dict[str, Any]],
    now_iso: str,
    enable_alias_mode: bool,
    target_fan_page_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        post_id = str(item.get("ID", "")).strip()
        if not post_id:
            continue
        if _is_already_scheduled_by_fan_page(item, target_fan_page_id):
            continue
        fan_page_entry = _extract_fan_page_entry(item, target_fan_page_id)
        categories = item.get("categories", [])
        if isinstance(categories, list) and categories:
            cat = str(categories[0]).strip().replace(" ", "")
        else:
            cat = str(item.get("category", "")).strip().replace(" ", "")
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


def _extract_data_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        data = payload.get("data", [])
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


@st.cache_data(show_spinner=False, ttl=60)
def sync_live_data_to_sample_files(enable_category_alias_mode: bool = False, target_fan_page_id: str = "") -> dict[str, Any]:
    try:
        api_base = _secret_or_env("API_BASE_URL")
        username = _secret_or_env("USERNAME")
        password = _secret_or_env("PASSWORD")
        basic_user = _secret_or_env("BASIC_AUTH_USERNAME")
        basic_pass = _secret_or_env("BASIC_AUTH_PASSWORD")
        posts_limit = int(_secret_or_env("API_POSTS_LIMIT", "10") or 10)

        if not api_base or not username or not password:
            return {"ok": False, "message": "missing API_BASE_URL/USERNAME/PASSWORD"}

        api_url, url_user, url_pass = _extract_basic_from_url(api_base)
        api_url = _normalize_endpoint_url(api_url)
        basic_user = basic_user or url_user
        basic_pass = basic_pass or url_pass
        gateway_basic_auth = ""
        if basic_user or basic_pass:
            raw = f"{basic_user}:{basic_pass}".encode("utf-8")
            gateway_basic_auth = f"Basic {base64.b64encode(raw).decode('ascii')}"

        login_headers = {"Content-Type": "application/json"}
        if gateway_basic_auth:
            login_headers["Authorization"] = gateway_basic_auth

        login_result = _json_post(
            api_url,
            {"action": "login", "username": username, "password": password},
            login_headers,
        )
        login_payload = login_result.get("response_json", {})
        token = str((login_payload.get("data", {}) if isinstance(login_payload, dict) else {}).get("token", "")).strip()
        if not login_result.get("ok") or not token:
            return {
                "ok": False,
                "message": f"login failed ({int(login_result.get('status_code', 0))})",
                "debug": {"login": login_result},
            }

        login_resp_headers = login_result.get("response_headers", {})
        session_cookie = str(login_resp_headers.get("Set-Cookie", "")).split(";", 1)[0].strip()
        common_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        if session_cookie:
            common_headers["Cookie"] = session_cookie

        published_result = _json_post(api_url, {"action": "fb_published"}, common_headers)
        published_result["auth_mode"] = "bearer"
        if not published_result.get("ok"):
            return {
                "ok": False,
                "message": f"fb_published failed ({int(published_result.get('status_code', 0))})",
                "debug": {"login": login_result, "fb_published": published_result},
            }
        scheduled_result = _json_post(api_url, {"action": "fb_scheduled"}, common_headers)
        scheduled_result["auth_mode"] = "bearer"
        if not scheduled_result.get("ok"):
            return {
                "ok": False,
                "message": f"fb_scheduled failed ({int(scheduled_result.get('status_code', 0))})",
                "debug": {"login": login_result, "fb_published": published_result, "fb_scheduled": scheduled_result},
            }

        now_iso = datetime.now(HKT_TZ).isoformat()
        fan_page_id = str(target_fan_page_id or _secret_or_env("TARGET_FAN_PAGE_ID", "350584865140118")).strip()
        pending_rows_all: list[dict[str, Any]] = []
        seen_pending: set[str] = set()
        posts_items_all: list[dict[str, Any]] = []
        for cat in CATEGORY_ORDER:
            posts_result = _json_post(
                api_url,
                {"action": "posts", "category": cat, "search": "", "limit": posts_limit},
                common_headers,
            )
            posts_result["auth_mode"] = "bearer"
            if not posts_result.get("ok"):
                return {
                    "ok": False,
                    "message": f"posts({cat}) failed ({int(posts_result.get('status_code', 0))})",
                    "debug": {
                        "login": login_result,
                        "fb_published": published_result,
                        "fb_scheduled": scheduled_result,
                        "posts_failed_category": cat,
                        "posts": posts_result,
                    },
                }
            posts_payload = posts_result.get("response_json", {})
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

        cms_id_by_post_link_id, cms_id_by_post_link = _build_cms_reference_maps(posts_items_all)
        published_rows = _to_published_rows(
            _extract_data_list(published_result.get("response_json", {})),
            enable_alias_mode=enable_category_alias_mode,
            cms_id_by_post_link_id=cms_id_by_post_link_id,
            cms_id_by_post_link=cms_id_by_post_link,
        )
        scheduled_thumb_fallback_map = _build_scheduled_thumb_map(pending_rows_all)
        scheduled_rows = _to_scheduled_rows(
            _extract_data_list(scheduled_result.get("response_json", {})),
            enable_alias_mode=enable_category_alias_mode,
            thumb_fallback_map=scheduled_thumb_fallback_map,
            cms_id_by_post_link_id=cms_id_by_post_link_id,
            cms_id_by_post_link=cms_id_by_post_link,
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
            "debug": {
                "login": login_result,
                "fb_published": published_result,
                "fb_scheduled": scheduled_result,
            },
        }
    except Exception as exc:  # noqa: BLE001 - keep dashboard alive on sync failure.
        return {"ok": False, "message": str(exc)}
