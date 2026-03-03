from datetime import datetime
from typing import Any


def build_schedule(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Placeholder scheduler. Branch feature/scheduler-dispatch owns full implementation."""
    scheduled = []
    for idx, item in enumerate(candidates):
        scheduled.append(
            {
                **item,
                "slot_index": idx,
                "scheduled_at": datetime.utcnow().isoformat(),
                "status": "pending_review",
            }
        )
    return scheduled

