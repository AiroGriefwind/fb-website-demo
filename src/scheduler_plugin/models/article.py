from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    id: int
    title: str
    category: str
    source_type: str
    heat_score: float = 0.0
    engagement_score: float = 0.0
    urgency_level: int = 0
    published_at: Optional[datetime] = None
    breaking_type: Optional[str] = None
    is_evergreen: bool = False
    social_share: bool = False
    is_scheduled: bool = False
    is_published_to_fb: bool = False
    is_high_engagement: bool = False
    has_video: bool = False
    item_id: str = ""
    soft_locked: bool = False
