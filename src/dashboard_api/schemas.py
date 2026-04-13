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

