from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from src.dashboard.config import HKT_TZ, PUBLISHED_FILE, SCHEDULED_FILE
from src.dashboard.data_utils import read_json_list
from src.dashboard.media_utils import parse_publish_time
from src.scheduler_plugin.time_provider import TimeProvider

logger = logging.getLogger(__name__)


def _parse_hkt_date_from_scheduled_row(row: dict[str, Any]) -> str | None:
    raw = str(row.get("publish_time", "") or "").strip()
    if not raw or "T" not in raw:
        return None
    try:
        dt = parse_publish_time(raw)
        if not dt:
            return None
        return dt.astimezone(HKT_TZ).date().isoformat()
    except Exception:
        return None


def run_nightly_repost_job() -> dict[str, Any]:
    """
    JSON/CMS-based nightly hook (no SQLite).
    Summarizes tomorrow repost slots vs high-engagement published rows for ops review.
    """
    tp = TimeProvider()
    tomorrow = (tp.now().date() + timedelta(days=1)).isoformat()

    published = read_json_list(PUBLISHED_FILE)
    scheduled = read_json_list(SCHEDULED_FILE)

    taken_times = {
        str(r.get("publish_time", ""))
        for r in scheduled
        if _parse_hkt_date_from_scheduled_row(r) == tomorrow
    }

    candidates: list[dict[str, Any]] = []
    for row in published:
        try:
            pc = float(row.get("popular_count") or row.get("views") or 0)
        except (TypeError, ValueError):
            pc = 0.0
        if pc < 50:
            continue
        candidates.append(
            {
                "item_id": str(row.get("item_id", "")),
                "title": str(row.get("title", ""))[:120],
                "popular_count": pc,
            }
        )
    candidates.sort(key=lambda x: x["popular_count"], reverse=True)
    top = candidates[:12]

    payload = {
        "status": "success",
        "target_date": tomorrow,
        "candidate_count": len(candidates),
        "top_candidates": top,
        "scheduled_rows_for_target_date": sum(1 for r in scheduled if _parse_hkt_date_from_scheduled_row(r) == tomorrow),
        "note": "Does not auto-write CMS; use dashboard publish or extend to call CmsActionClient.",
    }
    logger.info("repost_nightly: %s", payload)
    return payload
