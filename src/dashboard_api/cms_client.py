from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from dotenv import dotenv_values

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = WORKSPACE_ROOT / "configs" / ".env"
ENV_VALUES = {k: v for k, v in dotenv_values(ENV_PATH).items() if isinstance(v, str)}


def _env_value(key: str, default: str = "") -> str:
    value = os.getenv(key, "").strip()
    if value:
        return value
    file_value = str(ENV_VALUES.get(key, "")).strip()
    if file_value:
        return file_value
    return default


def _credential_value(primary_key: str, legacy_key: str, default: str = "") -> str:
    # Prefer explicit CMS_* keys, then project .env legacy keys, and finally process env.
    explicit = _env_value(primary_key, "")
    if explicit:
        return explicit
    legacy_file = str(ENV_VALUES.get(legacy_key, "")).strip()
    if legacy_file:
        return legacy_file
    legacy_env = os.getenv(legacy_key, "").strip()
    if legacy_env:
        return legacy_env
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
    base = raw_base_url.strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/index.php"):
        return base
    if base.endswith("/fb-scheduler"):
        return f"{base}/"
    return f"{base}/fb-scheduler/"


def _extract_token(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    data = payload.get("data", {})
    if isinstance(data, dict):
        token = str(data.get("token", "") or data.get("access_token", "")).strip()
        if token:
            return token
    return str(payload.get("token", "") or payload.get("access_token", "")).strip()


def _extract_message(payload: Any, fallback: str = "") -> str:
    if isinstance(payload, dict):
        for key in ("message", "error", "msg"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        nested = payload.get("data", {})
        if isinstance(nested, dict):
            for key in ("message", "error", "msg"):
                val = nested.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
    return fallback


def _build_basic_auth(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode("utf-8")
    return f"Basic {base64.b64encode(raw).decode('ascii')}"


def _json_post(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int = 45,
) -> tuple[bool, int, dict[str, str], Any, str]:
    body_text = json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False)
    body = body_text.encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"raw_text": text}
            return True, int(resp.getcode()), dict(resp.headers), data, ""
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw_text": text}
        return False, int(exc.code or 0), dict(exc.headers), data, str(exc.reason)
    except Exception as exc:  # noqa: BLE001
        return False, 0, {}, {}, str(exc)


class CmsActionClient:
    def __init__(self, *, use_production: bool = False) -> None:
        self._use_production = bool(use_production)
        raw_base = _env_value("PRODUCTION_API_BASE_URL") if self._use_production else _env_value("API_BASE_URL")
        raw_base, user_from_url, pass_from_url = _extract_basic_from_url(raw_base)
        self.base_url = _normalize_endpoint_url(raw_base)
        self.username = _credential_value("CMS_USERNAME", "USERNAME")
        self.password = _credential_value("CMS_PASSWORD", "PASSWORD")
        if self._use_production:
            self.basic_user = _env_value("PRODUCTION_BASIC_AUTH_USERNAME") or user_from_url
            self.basic_pass = _env_value("PRODUCTION_BASIC_AUTH_PASSWORD") or pass_from_url
        else:
            self.basic_user = _env_value("BASIC_AUTH_USERNAME") or user_from_url
            self.basic_pass = _env_value("BASIC_AUTH_PASSWORD") or pass_from_url
        self.login_cookies = _env_value("LOGIN_COOKIES")
        self._token = ""
        self._cookie = self.login_cookies

    def ready(self) -> tuple[bool, str]:
        if not self.base_url:
            return False, ("missing PRODUCTION_API_BASE_URL" if self._use_production else "missing API_BASE_URL")
        if not self.username or not self.password:
            return False, "missing USERNAME/PASSWORD"
        return True, ""

    def _login(self) -> tuple[bool, str]:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.basic_user or self.basic_pass:
            headers["Authorization"] = _build_basic_auth(self.basic_user, self.basic_pass)
        if self.login_cookies:
            headers["Cookie"] = self.login_cookies
        ok, status, resp_headers, resp_json, err = _json_post(
            self.base_url,
            {"action": "login", "username": self.username, "password": self.password},
            headers,
        )
        token = _extract_token(resp_json)
        cookie = str(resp_headers.get("Set-Cookie", "")).split(";", 1)[0].strip()
        if ok and token:
            self._token = token
            if cookie:
                self._cookie = cookie
            return True, ""
        return False, _extract_message(resp_json, err or f"login failed ({status})")

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self._use_production:
            if self.basic_user or self.basic_pass:
                headers["Authorization"] = _build_basic_auth(self.basic_user, self.basic_pass)
            headers["X-Token"] = self._token
            if self._cookie:
                headers["Cookies"] = self._cookie
            return headers
        headers["Authorization"] = f"Bearer {self._token}"
        if self._cookie:
            headers["Cookie"] = self._cookie
        return headers

    def run_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        ok_ready, ready_message = self.ready()
        if not ok_ready:
            return {"ok": False, "message": ready_message, "status_code": 0}
        if not self._token:
            ok_login, login_message = self._login()
            if not ok_login:
                return {"ok": False, "message": login_message, "status_code": 0}

        body = {"action": action, **payload}
        headers = self._auth_headers()
        ok, status, _, resp_json, err = _json_post(self.base_url, body, headers)
        if (not ok) and status in {401, 403}:
            ok_login, _ = self._login()
            if ok_login:
                ok, status, _, resp_json, err = _json_post(self.base_url, body, self._auth_headers())
        msg = _extract_message(resp_json, err or ("ok" if ok else f"{action} failed ({status})"))
        return {"ok": bool(ok), "message": "ok" if ok else msg, "status_code": status, "response_json": resp_json}

