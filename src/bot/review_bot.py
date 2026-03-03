from typing import Any


def format_review_message(item: dict[str, Any]) -> str:
    return (
        f"[待审核]\\n"
        f"title: {item.get('title', '')}\\n"
        f"final_score: {item.get('final_score', '')}\\n"
        f"scheduled_at: {item.get('scheduled_at', '')}"
    )

