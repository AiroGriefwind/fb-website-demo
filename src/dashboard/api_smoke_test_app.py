from __future__ import annotations

import base64
import http.client
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, parse, request

import streamlit as st
from dotenv import dotenv_values, load_dotenv

# Ensure imports like `from src...` work when launched via `streamlit run src/dashboard/api_smoke_test_app.py`.
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

ENV_PATH = WORKSPACE_ROOT / "configs" / ".env"
ENV_CONFIG = {k: v for k, v in dotenv_values(ENV_PATH).items() if isinstance(v, str)}
load_dotenv(dotenv_path=ENV_PATH, override=True)
DEBUG_LOG_PATH = WORKSPACE_ROOT / "debug-8a72c3.log"
DEBUG_SESSION_ID = "8a72c3"
DEBUG_RUN_ID = f"run-{int(time.time() * 1000)}"


def _env_value(key: str, default: str = "") -> str:
    value = ENV_CONFIG.get(key)
    if value is None:
        return default
    return value.strip() or default


def _normalize_target(base_url: str, endpoint_path: str) -> tuple[str, str, str]:
    base = base_url.strip().rstrip("/")
    endpoint = endpoint_path.strip()

    if not endpoint:
        if base.endswith("/fb-scheduler"):
            endpoint = "/"
        else:
            endpoint = "/fb-scheduler/"
    elif not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    full_url = f"{base}{endpoint}"
    return base, endpoint, full_url


def _safe_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _safe_json_decode(raw_text: str) -> Any:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw_text": raw_text}


def _extract_token(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None

    for key in ("token", "access_token"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    nested = data.get("data")
    if isinstance(nested, dict):
        for key in ("token", "access_token"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _build_basic_auth_value(username: str, password: str) -> str | None:
    if not username and not password:
        return None
    raw = f"{username}:{password}".encode("utf-8")
    return f"Basic {base64.b64encode(raw).decode('ascii')}"


def _set_x_token_for_basic_combo(headers: dict[str, str], token: str, *, bearer_prefix: bool) -> None:
    """網關 Basic + session token：token 走 X-Token（非 Token header）。"""
    headers["X-Token"] = f"Bearer {token}" if bearer_prefix else token


def _extract_basic_from_url(url: str) -> tuple[str, str | None]:
    parsed = parse.urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url, None

    if parsed.username is None and parsed.password is None:
        return url, None

    username = parse.unquote(parsed.username or "")
    password = parse.unquote(parsed.password or "")
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    sanitized = parse.urlunparse(
        (parsed.scheme, host, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )
    return sanitized, _build_basic_auth_value(username, password)


def _extract_set_cookie_value(headers: dict[str, Any]) -> str:
    value = headers.get("Set-Cookie") or headers.get("set-cookie") or ""
    if not isinstance(value, str) or not value.strip():
        return ""
    # Keep only the first cookie pair, e.g. PHPSESSID=xxxx
    return value.split(";", 1)[0].strip()


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
        # Debug logging must never break user request flow.
        pass


def _header_shape(headers: dict[str, str]) -> dict[str, Any]:
    auth_value = headers.get("Authorization", "")
    token_header = headers.get("X-Token", "") or headers.get("Token", "")
    token_shape = ""
    if token_header:
        token_shape = "bearer_prefixed" if token_header.startswith("Bearer ") else "raw_token"
    return {
        "has_authorization": "Authorization" in headers,
        "authorization_prefix": auth_value.split(" ", 1)[0] if auth_value else "",
        "has_proxy_authorization": "Proxy-Authorization" in headers,
        "has_token_header": "Token" in headers,
        "has_x_token_header": "X-Token" in headers,
        "token_shape": token_shape,
        "has_cookie_header": "Cookie" in headers,
        "has_cookies_header": "Cookies" in headers,
        "content_type": headers.get("Content-Type", ""),
    }


def _probe_request_shapes_on_401(
    url: str,
    posts_body: dict[str, Any],
    headers: dict[str, str],
    gateway_basic_auth: str | None,
) -> None:
    posts_min = {k: v for k, v in posts_body.items() if v is not None}
    posts_with_search = dict(posts_min)
    posts_with_search["search"] = ""
    bearer_auth = str(headers.get("Authorization", ""))
    token_header = str(headers.get("X-Token", "") or headers.get("Token", "")).strip()
    bearer_token = ""
    if bearer_auth.startswith("Bearer "):
        bearer_token = bearer_auth.replace("Bearer ", "", 1).strip()
    elif token_header:
        bearer_token = token_header.replace("Bearer ", "", 1).strip()
    cookie_value = str(headers.get("Cookie", "")).strip()

    if gateway_basic_auth and bearer_token:
        gateway_variants: list[tuple[str, dict[str, Any], str]] = [
            ("posts_json_basic_token_cookies", posts_with_search, "H23"),
            ("fb_published_json_basic_token_cookies", {"action": "fb_published", "limit": 1}, "H23"),
            ("posts_json_basic_token_bearer_cookies", posts_with_search, "H23"),
        ]
        for name, payload, hypothesis_id in gateway_variants:
            status_code = 0
            reason = ""
            body_preview = ""
            req_headers = {
                "Content-Type": "application/json",
                "Authorization": gateway_basic_auth,
                "Cookies": cookie_value,
            }
            if name.endswith("token_bearer_cookies"):
                req_headers["X-Token"] = f"Bearer {bearer_token}"
            else:
                req_headers["X-Token"] = bearer_token
            try:
                req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = request.Request(url, data=req_body, headers=req_headers, method="POST")
                with request.urlopen(req, timeout=20) as resp:
                    status_code = int(resp.getcode())
                    body_preview = resp.read().decode("utf-8", errors="replace")[:160]
            except error.HTTPError as exc:
                status_code = int(exc.code)
                reason = str(exc.reason)
                body_preview = exc.read().decode("utf-8", errors="replace")[:160]
            except Exception as exc:  # noqa: BLE001 - probe only
                reason = type(exc).__name__
            # region agent log
            _debug_log(
                hypothesis_id=hypothesis_id,
                location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                message="401 diagnostic gateway-header result",
                data={
                    "variant": name,
                    "status_code": status_code,
                    "reason": reason,
                    "header_shape": _header_shape(req_headers),
                    "payload_keys": sorted(payload.keys()),
                    "body_preview": body_preview,
                },
            )
            # endregion

        parsed = parse.urlsplit(url)
        host_root = parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        login_url = f"{host_root}/fb-scheduler/index.php"
        login_resp = post_json_with_headers(
            login_url,
            {"action": "login", "username": _env_value("USERNAME"), "password": _env_value("PASSWORD")},
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": gateway_basic_auth,
            },
            gateway_basic_auth=gateway_basic_auth,
        )
        fresh_token = _extract_token(login_resp.get("response_json")) or ""
        fresh_cookie = _extract_set_cookie_value(
            login_resp.get("response_headers", {})
            if isinstance(login_resp.get("response_headers", {}), dict)
            else {}
        )
        # region agent log
        _debug_log(
            hypothesis_id="H24",
            location="api_smoke_test_app.py:_probe_request_shapes_on_401",
            message="Fresh login for gateway-header probe",
            data={
                "login_status_code": int(login_resp.get("status_code", 0))
                if isinstance(login_resp.get("status_code"), int)
                else 0,
                "token_present": bool(fresh_token),
                "token_length": len(fresh_token),
                "cookie_present": bool(fresh_cookie),
            },
        )
        # endregion
        if fresh_token:
            for name, payload in [
                ("posts_json_basic_token_cookies_fresh", posts_with_search),
                ("fb_published_json_basic_token_cookies_fresh", {"action": "fb_published", "limit": 1}),
            ]:
                status_code = 0
                reason = ""
                body_preview = ""
                req_headers = {
                    "Content-Type": "application/json",
                    "Authorization": gateway_basic_auth,
                    "X-Token": fresh_token,
                    "Cookies": fresh_cookie,
                }
                try:
                    req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    req = request.Request(url, data=req_body, headers=req_headers, method="POST")
                    with request.urlopen(req, timeout=20) as resp:
                        status_code = int(resp.getcode())
                        body_preview = resp.read().decode("utf-8", errors="replace")[:160]
                except error.HTTPError as exc:
                    status_code = int(exc.code)
                    reason = str(exc.reason)
                    body_preview = exc.read().decode("utf-8", errors="replace")[:160]
                except Exception as exc:  # noqa: BLE001 - probe only
                    reason = type(exc).__name__
                # region agent log
                _debug_log(
                    hypothesis_id="H24",
                    location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                    message="Fresh token gateway-header result",
                    data={
                        "variant": name,
                        "status_code": status_code,
                        "reason": reason,
                        "header_shape": _header_shape(req_headers),
                        "payload_keys": sorted(payload.keys()),
                        "body_preview": body_preview,
                    },
                )
                # endregion

            parsed_host = parse.urlsplit(url)
            host = parsed_host.hostname or ""
            port = parsed_host.port
            if host:
                for variant_name, path, payload in [
                    ("posts_httpclient_double_slash", "//fb-scheduler/", posts_with_search),
                    ("posts_httpclient_single_slash", "/fb-scheduler/", posts_with_search),
                    ("fb_published_httpclient_double_slash", "//fb-scheduler/", {"action": "fb_published", "limit": 1}),
                    ("fb_published_httpclient_single_slash", "/fb-scheduler/", {"action": "fb_published", "limit": 1}),
                ]:
                    status_code = 0
                    reason = ""
                    body_preview = ""
                    req_headers = {
                        "Content-Type": "application/json",
                        "Authorization": gateway_basic_auth,
                        "X-Token": fresh_token,
                        "Cookies": fresh_cookie,
                    }
                    try:
                        if port:
                            conn = http.client.HTTPSConnection(host, port, timeout=20)
                        else:
                            conn = http.client.HTTPSConnection(host, timeout=20)
                        conn.request("POST", path, json.dumps(payload), req_headers)
                        resp = conn.getresponse()
                        status_code = int(resp.status)
                        reason = str(resp.reason)
                        body_preview = resp.read().decode("utf-8", errors="replace")[:160]
                        conn.close()
                    except Exception as exc:  # noqa: BLE001 - probe only
                        reason = type(exc).__name__
                    # region agent log
                    _debug_log(
                        hypothesis_id="H30",
                        location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                        message="Fresh token http.client slash variant",
                        data={
                            "variant": variant_name,
                            "path": path,
                            "status_code": status_code,
                            "reason": reason,
                            "header_shape": _header_shape(req_headers),
                            "body_preview": body_preview,
                        },
                    )
                    # endregion

                # Colleague-style Bearer-only probe (no cookie).
                colleague_status = 0
                colleague_reason = ""
                colleague_body_preview = ""
                colleague_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {fresh_token}",
                }
                colleague_payload = {
                    "action": "posts",
                    "category": "心韓",
                    "search": "",
                    "limit": 10,
                }
                try:
                    if port:
                        conn = http.client.HTTPSConnection(host, port, timeout=20)
                    else:
                        conn = http.client.HTTPSConnection(host, timeout=20)
                    conn.request("POST", "//fb-scheduler/", json.dumps(colleague_payload), colleague_headers)
                    colleague_resp = conn.getresponse()
                    colleague_status = int(colleague_resp.status)
                    colleague_reason = str(colleague_resp.reason)
                    colleague_body_preview = colleague_resp.read().decode("utf-8", errors="replace")[:160]
                    conn.close()
                except Exception as exc:  # noqa: BLE001 - probe only
                    colleague_reason = type(exc).__name__
                # region agent log
                _debug_log(
                    hypothesis_id="H31",
                    location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                    message="Colleague-style bearer probe result",
                    data={
                        "path": "//fb-scheduler/",
                        "status_code": colleague_status,
                        "reason": colleague_reason,
                        "header_shape": _header_shape(colleague_headers),
                        "body_preview": colleague_body_preview,
                    },
                )
                # endregion

            # Additional posts-only probes for path/body/header quirks.
            extra_posts_variants: list[tuple[str, str, str, dict[str, Any], dict[str, str]]] = [
                (
                    "posts_json_basic_token_cookies_fresh_indexphp",
                    "H26",
                    f"{host_root}/fb-scheduler/index.php",
                    posts_with_search,
                    {
                        "Content-Type": "application/json",
                        "Authorization": gateway_basic_auth,
                        "X-Token": fresh_token,
                        "Cookies": fresh_cookie,
                    },
                ),
                (
                    "posts_form_basic_token_cookies_fresh",
                    "H27",
                    url,
                    posts_with_search,
                    {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": gateway_basic_auth,
                        "X-Token": fresh_token,
                        "Cookies": fresh_cookie,
                    },
                ),
                (
                    "posts_json_basic_token_cookie_singular_fresh",
                    "H28",
                    url,
                    posts_with_search,
                    {
                        "Content-Type": "application/json",
                        "Authorization": gateway_basic_auth,
                        "X-Token": fresh_token,
                        "Cookie": fresh_cookie,
                    },
                ),
            ]

            for variant_name, hypothesis_id, variant_url, variant_payload, variant_headers in extra_posts_variants:
                status_code = 0
                reason = ""
                body_preview = ""
                try:
                    if variant_headers.get("Content-Type") == "application/x-www-form-urlencoded":
                        variant_body = parse.urlencode(variant_payload).encode("utf-8")
                    else:
                        variant_body = json.dumps(variant_payload, ensure_ascii=False).encode("utf-8")
                    req = request.Request(variant_url, data=variant_body, headers=variant_headers, method="POST")
                    with request.urlopen(req, timeout=20) as resp:
                        status_code = int(resp.getcode())
                        body_preview = resp.read().decode("utf-8", errors="replace")[:160]
                except error.HTTPError as exc:
                    status_code = int(exc.code)
                    reason = str(exc.reason)
                    body_preview = exc.read().decode("utf-8", errors="replace")[:160]
                except Exception as exc:  # noqa: BLE001 - probe only
                    reason = type(exc).__name__
                # region agent log
                _debug_log(
                    hypothesis_id=hypothesis_id,
                    location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                    message="Fresh token posts edge variant",
                    data={
                        "variant": variant_name,
                        "url": variant_url,
                        "status_code": status_code,
                        "reason": reason,
                        "header_shape": _header_shape(variant_headers),
                        "body_preview": body_preview,
                    },
                )
                # endregion

            for cat in ["心韓", "娛樂", "社會事"]:
                status_code = 0
                reason = ""
                body_preview = ""
                payload = {"action": "posts", "category": cat, "limit": 10, "search": ""}
                req_headers = {
                    "Content-Type": "application/json",
                    "Authorization": gateway_basic_auth,
                    "X-Token": fresh_token,
                    "Cookies": fresh_cookie,
                }
                try:
                    req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    req = request.Request(url, data=req_body, headers=req_headers, method="POST")
                    with request.urlopen(req, timeout=20) as resp:
                        status_code = int(resp.getcode())
                        body_preview = resp.read().decode("utf-8", errors="replace")[:160]
                except error.HTTPError as exc:
                    status_code = int(exc.code)
                    reason = str(exc.reason)
                    body_preview = exc.read().decode("utf-8", errors="replace")[:160]
                except Exception as exc:  # noqa: BLE001 - probe only
                    reason = type(exc).__name__
                # region agent log
                _debug_log(
                    hypothesis_id="H25",
                    location="api_smoke_test_app.py:_probe_request_shapes_on_401",
                    message="Fresh token posts category variant",
                    data={
                        "category": cat,
                        "status_code": status_code,
                        "reason": reason,
                        "header_shape": _header_shape(req_headers),
                        "body_preview": body_preview,
                    },
                )
                # endregion


def post_form(
    url: str,
    payload: dict[str, Any],
    token: str | None = None,
    cookies: str = "",
    gateway_basic_auth: str | None = None,
    auth_combo: str = "bearer_only",
    include_content_type: bool = True,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body_payload = {k: v for k, v in payload.items() if v is not None}
    encoded_text = parse.urlencode(body_payload)
    encoded = encoded_text.encode("utf-8")
    headers: dict[str, str] = {}
    if include_content_type:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if extra_headers:
        headers.update(extra_headers)
    if auth_combo in {"basic_token", "basic_token_bearer"} and gateway_basic_auth:
        headers["Authorization"] = gateway_basic_auth
        if token:
            _set_x_token_for_basic_combo(
                headers, token, bearer_prefix=(auth_combo == "basic_token_bearer")
            )
    elif token:
        headers["Authorization"] = f"Bearer {token}"
        if auth_combo == "proxy_bearer" and gateway_basic_auth:
            headers["Proxy-Authorization"] = gateway_basic_auth
    if cookies:
        cookie_header_name = "Cookies" if auth_combo in {"basic_token", "basic_token_bearer"} else "Cookie"
        headers[cookie_header_name] = cookies
    req = request.Request(url, data=encoded, headers=headers, method="POST")
    request_payload = {
        "method": "POST",
        "url": url,
        "headers": headers,
        "body_raw": encoded_text,
        "body_form": body_payload,
    }
    return _do_request(req, request_payload)


def post_json(
    url: str,
    payload: dict[str, Any],
    token: str | None = None,
    cookies: str = "",
    gateway_basic_auth: str | None = None,
    auth_combo: str = "bearer_only",
) -> dict[str, Any]:
    body_payload = {k: v for k, v in payload.items() if v is not None}
    encoded_text = json.dumps(body_payload, ensure_ascii=False)
    encoded = encoded_text.encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if auth_combo in {"basic_token", "basic_token_bearer"} and gateway_basic_auth:
        headers["Authorization"] = gateway_basic_auth
        if token:
            _set_x_token_for_basic_combo(
                headers, token, bearer_prefix=(auth_combo == "basic_token_bearer")
            )
    elif token:
        headers["Authorization"] = f"Bearer {token}"
        if auth_combo == "proxy_bearer" and gateway_basic_auth:
            headers["Proxy-Authorization"] = gateway_basic_auth
    if cookies:
        cookie_header_name = "Cookies" if auth_combo in {"basic_token", "basic_token_bearer"} else "Cookie"
        headers[cookie_header_name] = cookies
    body_shape = {
        "keys": sorted(body_payload.keys()),
        "has_action": "action" in body_payload,
        "has_category": "category" in body_payload,
        "has_search": "search" in body_payload,
        "search_is_empty_string": body_payload.get("search") == "",
        "has_limit": "limit" in body_payload,
        "limit_value": body_payload.get("limit") if "limit" in body_payload else None,
        "has_page": "page" in body_payload,
    }
    # region agent log
    _debug_log(
        hypothesis_id="H1-H2-H4-H9",
        location="api_smoke_test_app.py:post_json",
        message="Prepared post_json request headers",
        data={
            "action": str(body_payload.get("action", "")),
            "auth_combo": auth_combo,
            "has_token_argument": bool(token),
            "has_cookies_argument": bool(cookies),
            "header_shape": _header_shape(headers),
            "body_shape": body_shape,
        },
    )
    # endregion
    req = request.Request(url, data=encoded, headers=headers, method="POST")
    request_payload = {
        "method": "POST",
        "url": url,
        "headers": headers,
        "body_raw": encoded_text,
        "body_json": body_payload,
    }
    return _do_request(req, request_payload)


def post_json_with_headers(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    token: str | None = None,
    cookies: str = "",
    gateway_basic_auth: str | None = None,
    auth_combo: str = "bearer_only",
) -> dict[str, Any]:
    body_payload = {k: v for k, v in payload.items() if v is not None}
    encoded_text = json.dumps(body_payload, ensure_ascii=False)
    encoded = encoded_text.encode("utf-8")
    merged_headers = dict(headers)
    merged_headers.setdefault("Content-Type", "application/json; charset=utf-8")
    if auth_combo in {"basic_token", "basic_token_bearer"} and gateway_basic_auth:
        merged_headers["Authorization"] = gateway_basic_auth
        if token:
            _set_x_token_for_basic_combo(
                merged_headers, token, bearer_prefix=(auth_combo == "basic_token_bearer")
            )
    elif token:
        merged_headers["Authorization"] = f"Bearer {token}"
        if auth_combo == "proxy_bearer" and gateway_basic_auth:
            merged_headers["Proxy-Authorization"] = gateway_basic_auth
    if cookies:
        cookie_header_name = (
            "Cookies" if auth_combo in {"basic_token", "basic_token_bearer"} else "Cookie"
        )
        merged_headers[cookie_header_name] = cookies
    req = request.Request(url, data=encoded, headers=merged_headers, method="POST")
    request_payload = {
        "method": "POST",
        "url": url,
        "headers": merged_headers,
        "body_raw": encoded_text,
        "body_json": body_payload,
    }
    return _do_request(req, request_payload)


def _do_request(req: request.Request, request_payload: dict[str, Any]) -> dict[str, Any]:
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw_text = resp.read().decode("utf-8", errors="replace")
            # region agent log
            _debug_log(
                hypothesis_id="H1-H2-H3-H4",
                location="api_smoke_test_app.py:_do_request",
                message="HTTP success response",
                data={
                    "status_code": resp.getcode(),
                    "action": str((request_payload.get("body_json") or {}).get("action", "")),
                    "url": str(request_payload.get("url", "")),
                    "request_header_shape": _header_shape(
                        request_payload.get("headers", {})
                        if isinstance(request_payload.get("headers", {}), dict)
                        else {}
                    ),
                    "response_has_set_cookie": bool(resp.headers.get("Set-Cookie")),
                    "response_content_type": str(resp.headers.get("Content-Type", "")),
                },
            )
            # endregion
            return {
                "ok": True,
                "status_code": resp.getcode(),
                "request": request_payload,
                "response_headers": dict(resp.headers),
                "response_json": _safe_json_decode(raw_text),
            }
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        parsed_error_body = _safe_json_decode(body)
        # region agent log
        _debug_log(
            hypothesis_id="H1-H2-H3-H4-H5",
            location="api_smoke_test_app.py:_do_request",
            message="HTTP error response",
            data={
                "status_code": exc.code,
                "reason": str(exc.reason),
                "action": str((request_payload.get("body_json") or {}).get("action", "")),
                "url": str(request_payload.get("url", "")),
                "request_header_shape": _header_shape(
                    request_payload.get("headers", {})
                    if isinstance(request_payload.get("headers", {}), dict)
                    else {}
                ),
                "response_has_set_cookie": bool(exc.headers.get("Set-Cookie")),
                    "response_json_top_keys": sorted(list(parsed_error_body.keys()))
                    if isinstance(parsed_error_body, dict)
                    else [],
                    "response_json_error_message": str(
                        (
                            (parsed_error_body.get("message"))
                            if isinstance(parsed_error_body, dict)
                            else ""
                        )
                        or (
                            (parsed_error_body.get("error"))
                            if isinstance(parsed_error_body, dict)
                            else ""
                        )
                        or ""
                    )[:200],
                    "response_body_preview": body[:200],
            },
        )
        # endregion
        return {
            "ok": False,
            "status_code": exc.code,
            "request": request_payload,
            "response_headers": dict(exc.headers),
            "response_json": _safe_json_decode(body),
            "error": f"HTTPError: {exc.reason}",
        }
    except Exception as exc:  # noqa: BLE001 - smoke test app should show all failures.
        return {
            "ok": False,
            "request": request_payload,
            "error": str(exc),
        }


def ensure_login(
    base_url: str,
    username: str,
    password: str,
    gateway_basic_auth: str | None,
    login_cookies: str,
    use_gateway_mode: bool,
    as_json: bool = True,
) -> tuple[str | None, dict[str, Any]]:
    payload = {
        "action": "login",
        "username": username,
        "password": password,
    }
    login_extra_headers = {"Cookie": login_cookies} if login_cookies else {}
    login_gateway_auth = gateway_basic_auth if use_gateway_mode else None
    if login_gateway_auth:
        login_extra_headers["Authorization"] = login_gateway_auth
    if as_json:
        login_resp = post_json_with_headers(
            base_url,
            payload,
            headers=login_extra_headers,
            gateway_basic_auth=login_gateway_auth,
        )
    else:
        login_resp = post_form(
            base_url,
            payload,
            include_content_type=True,
            extra_headers=login_extra_headers,
            gateway_basic_auth=login_gateway_auth,
        )
    token = _extract_token(login_resp.get("response_json"))
    # region agent log
    _debug_log(
        hypothesis_id="H3-H4-H5",
        location="api_smoke_test_app.py:ensure_login",
        message="Login completed and token extracted",
        data={
            "use_gateway_mode": use_gateway_mode,
            "as_json": as_json,
            "login_status_code": int(login_resp.get("status_code", 0))
            if isinstance(login_resp.get("status_code"), int)
            else 0,
            "login_ok": bool(login_resp.get("ok")),
            "token_extracted": bool(token),
            "token_length": len(token or ""),
            "request_header_shape": _header_shape(
                login_resp.get("request", {}).get("headers", {})
                if isinstance(login_resp.get("request", {}), dict)
                else {}
            ),
            "response_has_set_cookie": bool(
                (
                    login_resp.get("response_headers", {})
                    if isinstance(login_resp.get("response_headers", {}), dict)
                    else {}
                ).get("Set-Cookie")
            ),
        },
    )
    # endregion
    return token, login_resp


def show_result(title: str, result: dict[str, Any]) -> None:
    req = result.get("request", {}) if isinstance(result.get("request", {}), dict) else {}
    body_only: Any = req.get("body_json")
    if body_only is None:
        body_only = req.get("body_form")
    if body_only is None:
        body_only = req.get("body_raw", {})

    if result.get("ok"):
        st.success(f"{title} 呼叫成功")
    else:
        st.error(f"{title} 呼叫失敗")
    st.markdown("**本次送出的請求體（Postman Body 對應）**")
    st.json(body_only)
    with st.expander("HTTP 完整請求（方法 / URL / Headers / Body）", expanded=False):
        st.json(req)
    st.json(result)


def main() -> None:
    # region agent log
    _debug_log(
        hypothesis_id="H0",
        location="api_smoke_test_app.py:main",
        message="App main entered",
        data={"workspace_root": str(WORKSPACE_ROOT)},
    )
    # endregion
    st.set_page_config(page_title="FB Scheduler API Smoke Test", page_icon="🧪", layout="wide")
    st.title("FB Scheduler API Smoke Test")
    st.caption("最小冒煙測試頁：逐一按按鈕即可測試對應 API，並顯示 JSON 回傳。")

    configured_base = (_env_value("API_BASE_URL") or _env_value("FB_SCHEDULER_BASE_URL") or "").strip()
    configured_base, basic_auth_from_url = _extract_basic_from_url(configured_base)
    configured_endpoint = _env_value("FB_SCHEDULER_ENDPOINT", "").strip()
    username = _env_value("USERNAME")
    password = _env_value("PASSWORD")
    basic_auth_user = _env_value("BASIC_AUTH_USERNAME")
    basic_auth_password = _env_value("BASIC_AUTH_PASSWORD")
    production_basic_user = _env_value("PRODUCTION_BASIC_AUTH_USERNAME")
    production_basic_password = _env_value("PRODUCTION_BASIC_AUTH_PASSWORD")
    login_cookies = _env_value("LOGIN_COOKIES")
    staging_gateway_basic_auth = basic_auth_from_url or _build_basic_auth_value(basic_auth_user, basic_auth_password)
    inferred_endpoint = "/fb-scheduler/"

    if configured_base:
        configured_base = configured_base.rstrip("/")
        if configured_base.endswith("/index.php"):
            configured_base = configured_base[: -len("/index.php")]
            inferred_endpoint = "/index.php"
        elif configured_base.endswith("/fb-scheduler"):
            inferred_endpoint = "/"

    default_base = configured_base
    default_endpoint = configured_endpoint or inferred_endpoint

    production_configured = _env_value("PRODUCTION_API_BASE_URL").strip()
    production_configured, basic_auth_from_production_url = _extract_basic_from_url(production_configured)
    if production_configured:
        production_configured = production_configured.rstrip("/")
        if production_configured.endswith("/index.php"):
            production_configured = production_configured[: -len("/index.php")]

    production_default_base = production_configured
    production_gateway_basic_auth = basic_auth_from_production_url or _build_basic_auth_value(
        production_basic_user,
        production_basic_password,
    )

    if "api_smoke_api_base" not in st.session_state:
        st.session_state.api_smoke_api_base = default_base

    prod_url_hint = production_default_base or "（請在 .env 設定 PRODUCTION_API_BASE_URL）"
    preset = st.radio(
        "API 環境",
        options=["Staging", "Production"],
        index=0,
        horizontal=True,
        help=(
            "Staging：Base URL 初始為 configs/.env 的 API_BASE_URL / FB_SCHEDULER_BASE_URL，"
            "網關 Basic 為 BASIC_AUTH_*（或 API URL 內嵌）。"
            f" Production：Base 為 PRODUCTION_API_BASE_URL（目前：{prod_url_hint}），"
            "網關 Basic 為 PRODUCTION_BASIC_AUTH_*（或該 URL 內嵌）。"
            "切換環境會清除已儲存的 Token，請重新 Login。"
        ),
        key="api_smoke_environment_preset",
    )
    last_preset = st.session_state.get("_api_smoke_last_preset_for_base")
    if last_preset != preset:
        if preset == "Staging":
            st.session_state.api_smoke_api_base = default_base
        else:
            st.session_state.api_smoke_api_base = production_default_base
        if last_preset is not None:
            st.session_state.api_token = None
        st.session_state._api_smoke_last_preset_for_base = preset

    col1, col2 = st.columns(2)
    with col1:
        api_base = st.text_input(
            "API Base URL (可含 /fb-scheduler)",
            key="api_smoke_api_base",
            placeholder="https://example.com",
            help="可用上方「API 環境」切換 Staging / Production；仍可在此手動覆寫或微調。",
        )
        st.text_input("Username (.env)", value=username, disabled=True)
    with col2:
        endpoint_path = st.text_input("Endpoint Path", value=default_endpoint)
        st.text_input("Password (.env)", value=password, type="password", disabled=True)

    if not api_base:
        st.warning("請先輸入 API Base URL，例如 https://your-domain.com")
        return
    if not username or not password:
        st.error("請先在 configs/.env 設定 USERNAME 與 PASSWORD。")
        return

    normalized_base, normalized_endpoint, full_url = _normalize_target(api_base, endpoint_path)
    normalized_base, basic_auth_from_input_url = _extract_basic_from_url(normalized_base)
    if basic_auth_from_input_url:
        gateway_basic_auth = basic_auth_from_input_url
        full_url = f"{normalized_base}{normalized_endpoint}"
    else:
        gateway_basic_auth = (
            production_gateway_basic_auth if preset == "Production" else staging_gateway_basic_auth
        )
    if normalized_base != api_base.strip().rstrip("/") or normalized_endpoint != endpoint_path.strip():
        st.info(f"已自動修正請求目標：base={normalized_base}  endpoint={normalized_endpoint}")
    st.code(full_url, language="text")

    if gateway_basic_auth:
        if preset == "Production":
            st.caption("已启用网关 Basic Auth（Production：PRODUCTION_BASIC_AUTH_* 或 PRODUCTION_API_BASE_URL 内嵌）。")
        else:
            st.caption("已启用网关 Basic Auth（Staging：BASIC_AUTH_* 或 API_BASE_URL 内嵌）。")
    else:
        if preset == "Production":
            st.caption("未检测到 Production 网关 Basic Auth（PRODUCTION_BASIC_AUTH_USERNAME / PRODUCTION_BASIC_AUTH_PASSWORD）。")
        else:
            st.caption("未检测到 Staging 网关 Basic Auth（BASIC_AUTH_USERNAME / BASIC_AUTH_PASSWORD）。")

    if "api_token" not in st.session_state:
        st.session_state.api_token = None
    if "api_cookies" not in st.session_state:
        st.session_state.api_cookies = login_cookies

    login_mode = st.radio(
        "Login Body 模式",
        options=["JSON", "FORM"],
        index=0,
        horizontal=True,
        help="默认 JSON（与你截图一致）；若服务端只收 form，可切 FORM 再试。",
    )
    login_auth_mode = st.radio(
        "Login Mode（僅控制登錄）",
        options=["網關模式(Basic)", "文檔模式(Bearer)"],
        index=0,
        horizontal=True,
        help="網關模式會帶 Basic；文檔模式不帶網關 Basic。",
    )
    use_login_gateway_mode = login_auth_mode == "網關模式(Basic)"
    api_auth_mode = st.radio(
        "後續 API Header 組合",
        options=[
            "Bearer only",
            "Proxy-Authorization + Bearer",
            "Basic + X-Token",
            "Basic + X-Token (Bearer)",
        ],
        index=2,
        horizontal=True,
        help=(
            "Production 網關：Authorization: Basic …；登入後的 session token 以 X-Token 傳遞。"
            " Basic+X-Token：X-Token 為裸 token；Basic+X-Token (Bearer)：X-Token 值為「Bearer 」前綴加 token。"
        ),
    )
    auth_combo = "bearer_only"
    if api_auth_mode == "Proxy-Authorization + Bearer":
        auth_combo = "proxy_bearer"
    elif api_auth_mode == "Basic + X-Token":
        auth_combo = "basic_token"
    elif api_auth_mode == "Basic + X-Token (Bearer)":
        auth_combo = "basic_token_bearer"
    if auth_combo in {"proxy_bearer", "basic_token", "basic_token_bearer"} and not gateway_basic_auth:
        st.warning("当前未检测到网关 Basic 凭证，所选组合可能缺少必要请求头。")

    if st.button("Login 取得 Token", use_container_width=True):
        token, login_result = ensure_login(
            full_url,
            username,
            password,
            gateway_basic_auth=gateway_basic_auth,
            login_cookies=login_cookies,
            use_gateway_mode=use_login_gateway_mode,
            as_json=(login_mode == "JSON"),
        )
        if token:
            st.session_state.api_token = token
            cookie_from_response = _extract_set_cookie_value(login_result.get("response_headers", {}))
            if cookie_from_response:
                st.session_state.api_cookies = cookie_from_response
        show_result("login", login_result)
        if token:
            st.info("Token 已更新到 session。")
        else:
            st.warning("Login 回傳中未找到 token 欄位，後續授權 API 可能失敗。")

    st.divider()
    st.subheader("Get Category Posts (action=posts)")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        category = st.text_input("category", value="娛樂", key="posts_category")
    with p_col2:
        posts_page = st.text_input("page (optional)", value="", key="posts_page")
    with p_col3:
        posts_limit = st.text_input("limit (optional)", value="", key="posts_limit")
    with p_col4:
        posts_search = st.text_input("search (optional)", value="", key="posts_search")

    if st.button("測試 Get Category Posts", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "posts",
            "category": category,
            "page": _safe_int(posts_page),
            "limit": _safe_int(posts_limit),
            "search": posts_search.strip() or None,
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("posts", result)
        if not result.get("ok") and int(result.get("status_code", 0) or 0) == 401:
            req_headers = {}
            if isinstance(result.get("request", {}), dict):
                headers_obj = result.get("request", {}).get("headers", {})
                if isinstance(headers_obj, dict):
                    req_headers = {str(k): str(v) for k, v in headers_obj.items()}
            _probe_request_shapes_on_401(full_url, payload, req_headers, gateway_basic_auth)

    st.divider()
    st.subheader("Get Facebook Page Published Posts (action=fb_published)")
    pub_col1, pub_col2 = st.columns(2)
    with pub_col1:
        pub_search = st.text_input("search (optional)", value="", key="pub_search")
    with pub_col2:
        pub_limit = st.text_input("limit (optional)", value="", key="pub_limit")

    if st.button("測試 Get Published Posts", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "fb_published",
            "search": pub_search.strip() or None,
            "limit": _safe_int(pub_limit),
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("fb_published", result)

    st.divider()
    st.subheader("Get Facebook Page Scheduled Posts (action=fb_scheduled)")
    sch_col1, sch_col2, sch_col3 = st.columns(3)
    with sch_col1:
        sch_search = st.text_input("search (optional)", value="", key="sch_search")
    with sch_col2:
        sch_limit = st.text_input("limit (optional)", value="", key="sch_limit")
    with sch_col3:
        sch_pages = st.text_input("pages (optional)", value="", key="sch_pages")

    if st.button("測試 Get Scheduled Posts", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "fb_scheduled",
            "search": sch_search.strip() or None,
            "limit": _safe_int(sch_limit),
            "pages": sch_pages.strip() or None,
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("fb_scheduled", result)

    st.divider()
    st.subheader("Publish Facebook Post (action=fb_publish)")
    default_time = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M")
    fbp_col1, fbp_col2, fbp_col3 = st.columns(3)
    with fbp_col1:
        fbp_post_id = st.number_input("post_id", min_value=1, step=1, value=1, key="fbp_post_id")
        fbp_type = st.selectbox("post_link_type", options=["link", "text", "photo", "video"], key="fbp_type")
    with fbp_col2:
        fbp_time = st.text_input("post_link_time (YYYY-MM-DDTHH:mm)", value=default_time, key="fbp_time")
        fbp_tz = st.text_input("post_timezone", value="Asia/Hong_Kong", key="fbp_tz")
    with fbp_col3:
        fbp_image_url = st.text_input("image_url (photo 時建議填)", value="", key="fbp_image")
        fbp_mp4_url = st.text_input("post_mp4_url (video 必填)", value="", key="fbp_mp4")
    fbp_message = st.text_area("post_message", value="Smoke test from Streamlit", key="fbp_message")

    if st.button("測試 Publish FB Post", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "fb_publish",
            "post_id": int(fbp_post_id),
            "post_message": fbp_message,
            "post_link_time": fbp_time.strip(),
            "post_link_type": fbp_type,
            "image_url": fbp_image_url.strip() or None,
            "post_mp4_url": fbp_mp4_url.strip() or None,
            "post_timezone": fbp_tz.strip() or "Asia/Hong_Kong",
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("fb_publish", result)

    st.divider()
    st.subheader("Update Facebook Post (action=fb_update)")
    fbu_col1, fbu_col2 = st.columns(2)
    with fbu_col1:
        fbu_post_id = st.number_input("post_id", min_value=1, step=1, value=1, key="fbu_post_id")
        fbu_post_link_id = st.text_input("post_link_id", value="", key="fbu_post_link_id")
        fbu_type = st.selectbox("post_link_type", options=["link", "text", "photo", "video"], key="fbu_type")
    with fbu_col2:
        fbu_time = st.text_input("post_link_time", value=default_time, key="fbu_time")
        fbu_message = st.text_area("post_message", value="Updated smoke test content", key="fbu_message")

    if st.button("測試 Update FB Post", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "fb_update",
            "post_id": int(fbu_post_id),
            "post_link_id": fbu_post_link_id.strip(),
            "post_message": fbu_message,
            "post_link_time": fbu_time.strip(),
            "post_link_type": fbu_type,
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("fb_update", result)

    st.divider()
    st.subheader("Delete Facebook Post (action=fb_delete)")
    fbd_col1, fbd_col2 = st.columns(2)
    with fbd_col1:
        fbd_post_id = st.number_input("post_id", min_value=1, step=1, value=1, key="fbd_post_id")
    with fbd_col2:
        fbd_post_link_id = st.text_input("post_link_id", value="", key="fbd_post_link_id")

    if st.button("測試 Delete FB Post", use_container_width=True):
        token = st.session_state.api_token
        if not token:
            token, login_result = ensure_login(
                full_url,
                username,
                password,
                gateway_basic_auth=gateway_basic_auth,
                login_cookies=login_cookies,
                use_gateway_mode=use_login_gateway_mode,
                as_json=(login_mode == "JSON"),
            )
            if token:
                st.session_state.api_token = token
            st.caption("先自動執行 login：")
            st.json(login_result)
        payload = {
            "action": "fb_delete",
            "post_id": int(fbd_post_id),
            "post_link_id": fbd_post_link_id.strip(),
        }
        result = post_json(
            full_url,
            payload,
            token=st.session_state.api_token,
            cookies=st.session_state.api_cookies,
            gateway_basic_auth=gateway_basic_auth,
            auth_combo=auth_combo,
        )
        show_result("fb_delete", result)


if __name__ == "__main__":
    main()
