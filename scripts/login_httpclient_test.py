from __future__ import annotations

import argparse
import base64
import http.client
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import dotenv_values


def load_config() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[1] / "configs" / ".env"
    raw = dotenv_values(env_path)
    config: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, str):
            config[key] = value.strip()
    return config


def build_target(api_base_url: str, endpoint_override: str | None) -> tuple[str, int | None, str]:
    parsed = urlparse(api_base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("API_BASE_URL 必须是 https://host[/path] 格式")

    host = parsed.hostname
    port = parsed.port

    if endpoint_override:
        endpoint = endpoint_override
    elif parsed.path and parsed.path != "/":
        endpoint = parsed.path
    else:
        endpoint = "/fb-scheduler/"

    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    return host, port, endpoint


def extract_basic_from_url(api_base_url: str) -> tuple[str, str]:
    parsed = urlparse(api_base_url)
    if parsed.username is None and parsed.password is None:
        return "", ""
    return unquote(parsed.username or ""), unquote(parsed.password or "")


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description="Login then posts smoke test via http.client")
    parser.add_argument(
        "--category",
        default="心韓",
        help="posts category",
    )
    parser.add_argument(
        "--search",
        default="",
        help="posts search",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="posts limit",
    )
    args = parser.parse_args()

    api_base_url = config.get("API_BASE_URL", "")
    username = config.get("USERNAME", "")
    password = config.get("PASSWORD", "")
    cookies_value = config.get("LOGIN_COOKIES", "")
    basic_user = config.get("BASIC_AUTH_USERNAME", "")
    basic_pass = config.get("BASIC_AUTH_PASSWORD", "")
    if not basic_user and not basic_pass:
        url_user, url_pass = extract_basic_from_url(api_base_url)
        basic_user = url_user
        basic_pass = url_pass

    if not api_base_url:
        raise ValueError("configs/.env 缺少 API_BASE_URL")
    if not username or not password:
        raise ValueError("configs/.env 缺少 USERNAME 或 PASSWORD")

    host, port, endpoint = build_target(api_base_url, config.get("API_LOGIN_PATH", "") or None)
    posts_endpoint = "//fb-scheduler/"

    login_payload = {
        "action": "login",
        "username": username,
        "password": password,
    }
    login_payload_raw = json.dumps(login_payload, ensure_ascii=False).encode("utf-8")
    login_headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    if cookies_value:
        login_headers["Cookie"] = cookies_value
    if basic_user or basic_pass:
        basic_raw = f"{basic_user}:{basic_pass}".encode("utf-8")
        login_headers["Authorization"] = f"Basic {base64.b64encode(basic_raw).decode('ascii')}"

    print("=== LOGIN REQUEST ===")
    if port:
        print(f"POST https://{host}:{port}{endpoint}")
    else:
        print(f"POST https://{host}{endpoint}")
    safe_headers = dict(login_headers)
    if "Authorization" in safe_headers:
        safe_headers["Authorization"] = "Basic ***"
    print("headers =", safe_headers)
    print("json body =", json.dumps(login_payload, ensure_ascii=False, indent=2))

    if port:
        conn = http.client.HTTPSConnection(host, port, timeout=30)
    else:
        conn = http.client.HTTPSConnection(host, timeout=30)
    conn.request("POST", endpoint, login_payload_raw, login_headers)
    res = conn.getresponse()
    login_data = res.read().decode("utf-8", errors="replace")
    set_cookie = res.getheader("Set-Cookie") or ""
    conn.close()

    print("\n=== LOGIN RESPONSE ===")
    print("status =", res.status)
    print("reason =", res.reason)
    print("body =", login_data)

    if res.status != 200:
        return

    try:
        token = str(json.loads(login_data).get("data", {}).get("token", "")).strip()
    except json.JSONDecodeError:
        token = ""
    if not token:
        print("login succeeded but token not found")
        return

    session_cookie = set_cookie.split(";", 1)[0].strip() if set_cookie else cookies_value
    posts_payload = {
        "action": "posts",
        "category": args.category,
        "search": args.search,
        "limit": args.limit,
    }
    posts_payload_raw = json.dumps(posts_payload, ensure_ascii=False).encode("utf-8")
    base_posts_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }
    variants: list[tuple[str, str]] = [("Cookie", "POSTS RESPONSE (Cookie)"), ("Cookies", "POSTS RESPONSE (Cookies)")]
    for cookie_header_name, response_title in variants:
        posts_headers = dict(base_posts_headers)
        if session_cookie:
            posts_headers[cookie_header_name] = session_cookie

        print(f"\n=== POSTS REQUEST ({cookie_header_name}) ===")
        if port:
            print(f"POST https://{host}:{port}{posts_endpoint}")
        else:
            print(f"POST https://{host}{posts_endpoint}")
        safe_posts_headers = dict(posts_headers)
        safe_posts_headers["Authorization"] = "Bearer ***"
        print("headers =", safe_posts_headers)
        print("json body =", json.dumps(posts_payload, ensure_ascii=False, indent=2))

        if port:
            conn = http.client.HTTPSConnection(host, port, timeout=30)
        else:
            conn = http.client.HTTPSConnection(host, timeout=30)
        conn.request("POST", posts_endpoint, posts_payload_raw, posts_headers)
        posts_res = conn.getresponse()
        posts_data = posts_res.read().decode("utf-8", errors="replace")
        conn.close()

        print(f"\n=== {response_title} ===")
        print("status =", posts_res.status)
        print("reason =", posts_res.reason)
        print("body =", posts_data)


if __name__ == "__main__":
    main()
