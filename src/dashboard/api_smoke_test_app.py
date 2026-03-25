from __future__ import annotations

import base64
import json
import os
import sys
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


def post_form(
    url: str,
    payload: dict[str, Any],
    token: str | None = None,
    cookies: str = "",
    gateway_basic_auth: str | None = None,
    prefer_bearer: bool = False,
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
    if prefer_bearer and token:
        headers["Authorization"] = f"Bearer {token}"
        if gateway_basic_auth:
            headers["Proxy-Authorization"] = gateway_basic_auth
    elif gateway_basic_auth:
        headers["Authorization"] = gateway_basic_auth
        if token:
            headers["Token"] = token
    elif token:
        headers["Authorization"] = f"Bearer {token}"
    if cookies:
        headers["Cookie"] = cookies
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
    prefer_bearer: bool = False,
) -> dict[str, Any]:
    body_payload = {k: v for k, v in payload.items() if v is not None}
    encoded_text = json.dumps(body_payload, ensure_ascii=False)
    encoded = encoded_text.encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if prefer_bearer and token:
        headers["Authorization"] = f"Bearer {token}"
        if gateway_basic_auth:
            headers["Proxy-Authorization"] = gateway_basic_auth
    elif gateway_basic_auth:
        headers["Authorization"] = gateway_basic_auth
        if token:
            headers["Token"] = token
    elif token:
        headers["Authorization"] = f"Bearer {token}"
    if cookies:
        headers["Cookie"] = cookies
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
    prefer_bearer: bool = False,
) -> dict[str, Any]:
    body_payload = {k: v for k, v in payload.items() if v is not None}
    encoded_text = json.dumps(body_payload, ensure_ascii=False)
    encoded = encoded_text.encode("utf-8")
    merged_headers = dict(headers)
    merged_headers.setdefault("Content-Type", "application/json")
    if prefer_bearer and token:
        merged_headers["Authorization"] = f"Bearer {token}"
        if gateway_basic_auth:
            merged_headers["Proxy-Authorization"] = gateway_basic_auth
    elif gateway_basic_auth:
        merged_headers["Authorization"] = gateway_basic_auth
        if token:
            merged_headers["Token"] = token
    elif token:
        merged_headers["Authorization"] = f"Bearer {token}"
    if cookies:
        merged_headers["Cookie"] = cookies
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
            return {
                "ok": True,
                "status_code": resp.getcode(),
                "request": request_payload,
                "response_headers": dict(resp.headers),
                "response_json": _safe_json_decode(raw_text),
            }
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
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
    login_cookies = _env_value("LOGIN_COOKIES")
    gateway_basic_auth = basic_auth_from_url or _build_basic_auth_value(basic_auth_user, basic_auth_password)
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

    col1, col2 = st.columns(2)
    with col1:
        api_base = st.text_input(
            "API Base URL (可含 /fb-scheduler)",
            value=default_base,
            placeholder="https://example.com",
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
    if normalized_base != api_base.strip().rstrip("/") or normalized_endpoint != endpoint_path.strip():
        st.info(f"已自動修正請求目標：base={normalized_base}  endpoint={normalized_endpoint}")
    st.code(full_url, language="text")
    if gateway_basic_auth:
        st.caption("已启用网关 Basic Auth（从 .env 读取）。")
    else:
        st.caption("未检测到网关 Basic Auth（BASIC_AUTH_USERNAME / BASIC_AUTH_PASSWORD）。")

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
        "後續 API 鑑權模式",
        options=["文檔模式(Bearer)", "網關模式(Basic+Token)"],
        index=0,
        horizontal=True,
        help="网关模式更易通过 ELB；文档模式严格按 Authorization: Bearer <TOKEN>。",
    )
    use_doc_bearer = api_auth_mode == "文檔模式(Bearer)"

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
            prefer_bearer=use_doc_bearer,
        )
        show_result("posts", result)

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
            prefer_bearer=use_doc_bearer,
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
            prefer_bearer=use_doc_bearer,
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
            prefer_bearer=use_doc_bearer,
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
            prefer_bearer=use_doc_bearer,
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
            prefer_bearer=use_doc_bearer,
        )
        show_result("fb_delete", result)


if __name__ == "__main__":
    main()
