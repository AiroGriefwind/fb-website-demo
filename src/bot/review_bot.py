from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import parse, request


class TelegramAPIError(RuntimeError):
    """Raised when Telegram Bot API returns a non-ok response."""


@dataclass(frozen=True)
class TelegramMessageResult:
    ok: bool
    message_id: int | None
    raw_response: dict[str, Any]


def _telegram_api_call(
    token: str, method: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not token:
        raise ValueError("Telegram bot token is required.")

    url = f"https://api.telegram.org/bot{token}/{method}"
    encoded = parse.urlencode(payload or {}).encode("utf-8")
    req = request.Request(url=url, data=encoded, method="POST")
    with request.urlopen(req, timeout=15) as resp:  # nosec B310
        body = resp.read().decode("utf-8")

    data = json.loads(body)
    if not data.get("ok"):
        description = data.get("description", "Unknown Telegram API error.")
        raise TelegramAPIError(f"{method} failed: {description}")
    return data


def get_bot_profile(token: str) -> dict[str, Any]:
    """Validate token and return bot profile from Telegram."""
    return _telegram_api_call(token=token, method="getMe", payload={}).get("result", {})


def send_text_message(token: str, chat_id: str, text: str) -> TelegramMessageResult:
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "disable_web_page_preview": "true",
    }
    data = _telegram_api_call(token=token, method="sendMessage", payload=payload)
    message = data.get("result", {})
    return TelegramMessageResult(
        ok=True,
        message_id=message.get("message_id"),
        raw_response=data,
    )


def format_review_message(item: dict[str, Any]) -> str:
    return (
        "[待审核]\n"
        f"run_id: {item.get('run_id', '')}\n"
        f"title: {item.get('title', '')}\n"
        f"reached: {item.get('reached', 0)}\n"
        f"engaged: {item.get('engaged', 0)}\n"
        f"final_score: {item.get('final_score', '')}\n"
        f"scheduled_at: {item.get('scheduled_at', '')}"
    )


def send_review_message(
    token: str, chat_id: str, item: dict[str, Any]
) -> TelegramMessageResult:
    return send_text_message(token=token, chat_id=chat_id, text=format_review_message(item))

