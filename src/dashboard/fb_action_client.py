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

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = WORKSPACE_ROOT / "configs" / ".env"
ENV_VALUES = {k: v for k, v in dotenv_values(ENV_PATH).items() if isinstance(v, str)}
LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_FILE = LOG_DIR / "dashboard_fb_actions.jsonl"


def _secret_or_env(key: str, default: str = "") -> str:
    value = ""
    try:
        if key in st.secrets:
            value = str(st.secrets.get(key, "") or "").strip()
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


def _build_basic_auth(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode("utf-8")
    return f"Basic {base64.b64encode(raw).decode('ascii')}"


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
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("message", "error", "msg"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
    return fallback


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, val in headers.items():
        low = key.lower()
        if low in {"authorization", "proxy-authorization", "token", "cookie"}:
            safe[key] = "***"
        else:
            safe[key] = val
    return safe


def _append_log(record: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")


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
            return True, resp.getcode(), dict(resp.headers), data, ""
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"raw_text": text}
        return False, int(exc.code or 0), dict(exc.headers), data, str(exc.reason)
    except Exception as exc:  # noqa: BLE001
        return False, 0, {}, {}, str(exc)


class FBActionClient:
    def __init__(self) -> None:
        raw_base = _secret_or_env("API_BASE_URL")
        raw_base, user_from_url, pass_from_url = _extract_basic_from_url(raw_base)
        self.base_url = _normalize_endpoint_url(raw_base)
        self.username = _secret_or_env("USERNAME")
        self.password = _secret_or_env("PASSWORD")
        self.basic_user = _secret_or_env("BASIC_AUTH_USERNAME") or user_from_url
        self.basic_pass = _secret_or_env("BASIC_AUTH_PASSWORD") or pass_from_url
        self.login_cookies = _secret_or_env("LOGIN_COOKIES")
        self._token: str = str(st.session_state.get("fb_action_token", "")).strip()
        self._cookie: str = str(st.session_state.get("fb_action_cookie", self.login_cookies)).strip()

    def ready(self) -> tuple[bool, str]:
        if not self.base_url:
            return False, "缺少 API_BASE_URL，无法调用 FB 动作 API。"
        if not self.username or not self.password:
            return False, "缺少 USERNAME/PASSWORD，无法调用 FB 动作 API。"
        return True, ""

    def _login(self) -> tuple[bool, str, dict[str, Any]]:
        login_headers = {"Content-Type": "application/json"}
        if self.basic_user or self.basic_pass:
            login_headers["Authorization"] = _build_basic_auth(self.basic_user, self.basic_pass)
        if self.login_cookies:
            login_headers["Cookie"] = self.login_cookies
        ok, status, resp_headers, resp_json, err = _json_post(
            self.base_url,
            {"action": "login", "username": self.username, "password": self.password},
            login_headers,
        )
        token = _extract_token(resp_json)
        set_cookie = str(resp_headers.get("Set-Cookie", "")).split(";", 1)[0].strip()
        if ok and token:
            self._token = token
            st.session_state["fb_action_token"] = token
            if set_cookie:
                self._cookie = set_cookie
                st.session_state["fb_action_cookie"] = set_cookie
            elif self.login_cookies:
                self._cookie = self.login_cookies
                st.session_state["fb_action_cookie"] = self.login_cookies
            return True, "", {"status_code": status, "response_json": resp_json}
        msg = _extract_message(resp_json, err or f"login failed ({status})")
        return False, msg, {"status_code": status, "response_json": resp_json}

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }
        if self._cookie:
            headers["Cookie"] = self._cookie
        return headers

    def run_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        ok_ready, ready_msg = self.ready()
        if not ok_ready:
            return {"ok": False, "message": ready_msg, "status_code": 0, "response_json": {}}

        if not self._token:
            ok_login, msg_login, login_raw = self._login()
            if not ok_login:
                self._write_action_log(action, payload, 0, {}, {"login": login_raw}, msg_login)
                return {"ok": False, "message": msg_login, "status_code": 0, "response_json": {"login": login_raw}}

        body = {"action": action, **payload}
        headers = self._auth_headers()
        ok, status, _, resp_json, err = _json_post(self.base_url, body, headers)

        msg = _extract_message(resp_json, err or ("ok" if ok else f"{action} failed ({status})"))
        self._write_action_log(action, body, status, headers, resp_json, msg if not ok else "")
        return {
            "ok": bool(ok),
            "message": "操作成功" if ok else msg,
            "status_code": status,
            "response_json": resp_json,
            "log_file": str(LOG_FILE),
        }

    def _write_action_log(
        self,
        action: str,
        body: dict[str, Any],
        status: int,
        headers: dict[str, str],
        response_json: Any,
        error_message: str,
    ) -> None:
        record = {
            "ts": datetime.now().isoformat(),
            "action": action,
            "status_code": status,
            "ok": not bool(error_message),
            "request": {"url": self.base_url, "headers": _sanitize_headers(headers), "body": body},
            "response_json": response_json,
            "error": error_message,
        }
        _append_log(record)

    def publish_post(
        self,
        *,
        post_id: int,
        post_message: str,
        post_link_time: str,
        post_link_type: str,
        image_url: str = "",
        post_mp4_url: str = "",
        post_timezone: str = "Asia/Hong_Kong",
    ) -> dict[str, Any]:
        return self.run_action(
            "fb_publish",
            {
                "post_id": int(post_id),
                "post_message": post_message,
                "post_link_time": post_link_time,
                "post_link_type": post_link_type,
                "image_url": image_url.strip() or None,
                "post_mp4_url": post_mp4_url.strip() or None,
                "post_timezone": post_timezone,
            },
        )

    def update_post(
        self,
        *,
        post_id: int,
        post_link_id: str,
        post_message: str,
        post_link_time: str,
        post_link_type: str,
        image_url: str = "",
        post_mp4_url: str = "",
    ) -> dict[str, Any]:
        return self.run_action(
            "fb_update",
            {
                "post_id": int(post_id),
                "post_link_id": post_link_id.strip(),
                "post_message": post_message,
                "post_link_time": post_link_time,
                "post_link_type": post_link_type,
                "image_url": image_url.strip() or None,
                "post_mp4_url": post_mp4_url.strip() or None,
            },
        )

    def delete_post(self, *, post_id: int, post_link_id: str) -> dict[str, Any]:
        return self.run_action(
            "fb_delete",
            {
                "post_id": int(post_id),
                "post_link_id": post_link_id.strip(),
            },
        )
