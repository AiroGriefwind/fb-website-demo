from __future__ import annotations

from datetime import datetime
from typing import Any

from src.dashboard.config import HKT_TZ
from src.scheduler_plugin.adapter import (
    articles_from_pending_rows,
    article_from_published_row,
    engine_category_to_board_display,
    merge_article_lists,
)
from src.scheduler_plugin.services.scheduler_engine import SchedulerEngine
from src.scheduler_plugin.time_provider import TimeProvider

ENTERTAINMENT_CATEGORIES = {"娛圈事", "心韓", "娛樂"}
SOCIAL_TEXT_CATEGORIES = {"社會事", "大視野", "兩岸", "法庭事", "消費", "商業事"}


def _resolve_now(*, schedule_date: str, time_provider: TimeProvider | None = None) -> datetime:
    tp = time_provider or TimeProvider()
    current = tp.now()
    if not schedule_date.strip():
        return current
    schedule_date_obj = datetime.strptime(schedule_date.strip(), "%Y-%m-%d").date()
    if schedule_date_obj == current.date():
        return current
    return datetime.combine(schedule_date_obj, datetime.min.time(), tzinfo=HKT_TZ)


def _resolve_suggested_post_type(*, category: str, is_repost: bool, has_video: bool) -> str:
    """
    Align with teammate's post-type defaults:
    - repost lane -> link_post
    - entertainment -> photo_post (or video_post when video exists)
    - social lanes -> text_post
    """
    if is_repost:
        return "link_post"
    if category in ENTERTAINMENT_CATEGORIES:
        return "video_post" if has_video else "photo_post"
    if category in SOCIAL_TEXT_CATEGORIES:
        return "text_post"
    return "text_post"


def generate_schedule_suggestions(
    *,
    pending_rows: list[dict[str, Any]],
    published_rows: list[dict[str, Any]] | None = None,
    schedule_date: str,
    include_published_for_repost: bool = True,
    repost_engagement_threshold: float = 50.0,
) -> dict[str, Any]:
    pending_articles = articles_from_pending_rows(pending_rows)
    extra: list = []
    if include_published_for_repost and published_rows:
        for row in published_rows:
            a = article_from_published_row(row, engagement_threshold=repost_engagement_threshold)
            if a:
                extra.append(a)
    articles = merge_article_lists(pending_articles, extra)
    if not articles:
        return {"ok": False, "message": "no articles to schedule", "schedule": [], "count": 0}

    now = _resolve_now(schedule_date=schedule_date)
    engine = SchedulerEngine()
    draft = engine.run(now, articles)

    schedule_out: list[dict[str, Any]] = []
    for slot_dt, art in sorted(draft.items(), key=lambda x: x[0]):
        display_cat = engine_category_to_board_display(art.category)
        suggested_post_type = _resolve_suggested_post_type(
            category=str(art.category or ""),
            is_repost=bool(art.is_published_to_fb),
            has_video=bool(getattr(art, "has_video", False)),
        )
        schedule_out.append(
            {
                "schedule_time": slot_dt.astimezone(HKT_TZ).strftime("%Y-%m-%dT%H:%M"),
                "item_id": str(art.item_id or art.id),
                "post_id": int(art.id),
                "title": art.title,
                "category_display": display_cat,
                "engine_category": art.category,
                "is_repost": bool(art.is_published_to_fb),
                "suggested_post_type": suggested_post_type,
            }
        )

    return {
        "ok": True,
        "message": "ok",
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "schedule": schedule_out,
        "count": len(schedule_out),
    }
