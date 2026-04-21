from __future__ import annotations

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    item_id: str = Field(..., min_length=1)
    schedule_time: str = Field(..., description="YYYY-MM-DDTHH:mm in HKT")
    window_minutes: int = 10
    post_message: str = ""
    post_link_type: str = "link"
    image_url: str = ""
    immediate_publish: bool = False
    allow_shift: bool = False
    schedule_method: str = "manual_user"


class UpdateRequest(BaseModel):
    post_id: int
    post_link_id: str
    post_message: str
    post_link_time: str = Field(..., description="YYYY-MM-DDTHH:mm wall time in HKT; server converts to UTC for FB")
    post_link_type: str = "link"
    image_url: str = ""
    post_mp4_url: str = ""
    enforce_time_validation: bool = True
    target_action_key: str = ""
    window_minutes: int = 10
    immediate_publish: bool = False
    allow_shift: bool = False
    schedule_method: str = "manual_user"


class DeleteRequest(BaseModel):
    post_id: int
    post_link_id: str


class ToggleLockRequest(BaseModel):
    action_key: str = Field(..., min_length=1)


class BoardColumnsResponse(BaseModel):
    published: list[dict]
    scheduled: list[dict]
    pending_by_category: dict[str, list[dict]]
    generated_at: str
    # Populated when board load triggers live sync (browser → FastAPI → CMS).
    cms_upstream_calls: list[dict] = Field(default_factory=list)


class SchedulerGenerateRequest(BaseModel):
    schedule_date: str = Field(..., description="Anchor date YYYY-MM-DD (HKT calendar day)")
    sync: bool = Field(default=True, description="Run live CMS sync before reading sample pending/published")
    include_published_for_repost: bool = Field(default=True)
    repost_engagement_threshold: float = Field(default=50.0)


class SchedulerApplyItem(BaseModel):
    item_id: str = Field(..., min_length=1)
    schedule_time: str = Field(default="", description="YYYY-MM-DDTHH:mm HKT; ignored when immediate_publish")
    immediate_publish: bool = False
    window_minutes: int = Field(default=10, ge=1, le=60)
    post_message: str = ""
    post_link_type: str = "link"
    image_url: str = ""
    allow_shift: bool = True
    schedule_method: str = "auto_plugin"


class SchedulerApplyRequest(BaseModel):
    items: list[SchedulerApplyItem] = Field(default_factory=list)
    stop_on_error: bool = True

