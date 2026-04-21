from __future__ import annotations

from datetime import datetime
from typing import Any

from src.scheduler_plugin.models.article import Article

# Board column labels (dashboard) -> engine slot categories (schedule_config)
BOARD_TO_ENGINE_CATEGORY: dict[str, str] = {
    "娛樂": "娛圈事",
    "社會事": "社會事",
    "大視野": "大視野",
    "兩岸": "兩岸",
    "法庭事": "法庭事",
    "消費": "消費",
    "心韓": "心韓",
}

# CMS / legacy source buckets → treat as social feed for scheduling
_DEFAULT_SOCIAL = "社會事"


def engine_category_to_board_display(engine_cat: str) -> str:
    rev = {v: k for k, v in BOARD_TO_ENGINE_CATEGORY.items()}
    return rev.get(engine_cat, engine_cat)


def _safe_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def _normalize_source_category(raw: str) -> str:
    s = (raw or "").strip()
    if s in BOARD_TO_ENGINE_CATEGORY:
        return BOARD_TO_ENGINE_CATEGORY[s]
    if s in ("娛圈事", "社會事", "大視野", "兩岸", "法庭事", "消費", "商業事", "心韓", "plastic"):
        return s
    if s.upper().startswith("SOURCE") or s in ("SourceR", "SourceD", "未分類", ""):
        return _DEFAULT_SOCIAL
    return _DEFAULT_SOCIAL


def article_from_pending_row(row: dict[str, Any]) -> Article:
    post_id = _safe_int(row.get("post_id", 0))
    item_id = str(row.get("item_id", "") or "").strip()
    aid = post_id if post_id > 0 else abs(hash(item_id)) % (10**9) if item_id else 0
    cat = _normalize_source_category(str(row.get("category", "")))
    popular = float(row.get("popular_count") or 0)
    pub_raw = row.get("publish_time")
    published_at: datetime | None = None
    if isinstance(pub_raw, str) and pub_raw.strip():
        try:
            published_at = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
        except ValueError:
            published_at = None
    has_video = bool(
        str(row.get("post_mp4_url", "") or "").strip()
        or str(row.get("video_url", "") or "").strip()
        or str(row.get("mp4_url", "") or "").strip()
        or (isinstance(row.get("videos"), list) and len(row.get("videos") or []) > 0)
    )
    return Article(
        id=aid,
        title=str(row.get("title", "") or ""),
        category=cat,
        source_type="cms_pending",
        heat_score=popular,
        engagement_score=float(row.get("engagements") or 0),
        urgency_level=_safe_int(row.get("urgency_level", 0)),
        published_at=published_at,
        breaking_type=row.get("breaking_type"),
        social_share=bool(row.get("social_media_share", False)),
        is_published_to_fb=False,
        is_high_engagement=False,
        has_video=has_video,
        item_id=item_id or str(aid),
    )


def articles_from_pending_rows(rows: list[dict[str, Any]]) -> list[Article]:
    return [article_from_pending_row(r) for r in rows if r]


def article_from_published_row(row: dict[str, Any], *, engagement_threshold: float = 50.0) -> Article | None:
    post_id = _safe_int(row.get("post_id", 0))
    item_id = str(row.get("item_id", "") or "").strip()
    aid = post_id if post_id > 0 else 0
    if aid <= 0 and not item_id:
        return None
    if aid <= 0:
        aid = abs(hash(item_id)) % (10**9)
    popular = float(row.get("popular_count") or row.get("views") or 0)
    cat = _normalize_source_category(str(row.get("category", "")))
    has_video = bool(
        str(row.get("post_mp4_url", "") or "").strip()
        or str(row.get("video_url", "") or "").strip()
        or str(row.get("mp4_url", "") or "").strip()
        or (isinstance(row.get("videos"), list) and len(row.get("videos") or []) > 0)
    )
    return Article(
        id=aid,
        title=str(row.get("title", "") or ""),
        category=cat,
        source_type="cms_published",
        heat_score=popular,
        is_published_to_fb=True,
        is_high_engagement=popular >= engagement_threshold,
        has_video=has_video,
        item_id=item_id or str(aid),
    )


def merge_article_lists(*lists: list[Article]) -> list[Article]:
    by_id: dict[int, Article] = {}
    for lst in lists:
        for a in lst:
            by_id[a.id] = a
    return list(by_id.values())
