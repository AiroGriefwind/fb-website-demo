from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.scheduler_plugin.adapter import article_from_pending_row, engine_category_to_board_display
from src.scheduler_plugin.pipeline import generate_schedule_suggestions
from src.dashboard.config import HKT_TZ
from src.dashboard_api.services import _plan_publish_slot_adjustments


def test_engine_category_roundtrip_display():
    assert engine_category_to_board_display("娛圈事") == "娛樂"


def test_article_from_pending_maps_entertainment():
    row = {
        "item_id": "99",
        "post_id": 99,
        "title": "t",
        "category": "娛樂",
        "popular_count": 12,
        "publish_time": "2026-01-01T10:00:00Z",
    }
    a = article_from_pending_row(row)
    assert a.category == "娛圈事"
    assert a.item_id == "99"


def test_generate_schedule_slots_are_sorted_and_hkt_shape():
    pending = [
        {
            "item_id": str(1000 + i),
            "post_id": 1000 + i,
            "title": f"Article {i}",
            "category": "社會事",
            "popular_count": i,
            "publish_time": "2026-04-21T08:00:00Z",
        }
        for i in range(30)
    ]
    out = generate_schedule_suggestions(
        pending_rows=pending,
        published_rows=None,
        schedule_date="2026-04-21",
        include_published_for_repost=False,
    )
    assert out["ok"] is True
    sched = out["schedule"]
    assert len(sched) >= 1
    times = [x["schedule_time"] for x in sched]
    assert times == sorted(times)
    for x in sched:
        assert len(x["schedule_time"]) >= 16
        assert x["schedule_time"][4] == "-"
        assert "T" in x["schedule_time"]


def test_post_type_rules_social_and_entertainment():
    pending = [
        {
            "item_id": "a1",
            "post_id": 101,
            "title": "social",
            "category": "社會事",
            "popular_count": 50,
            "publish_time": "2026-04-21T08:00:00Z",
        },
        {
            "item_id": "a2",
            "post_id": 102,
            "title": "ent-photo",
            "category": "娛樂",
            "popular_count": 90,
            "publish_time": "2026-04-21T08:00:00Z",
        },
        {
            "item_id": "a3",
            "post_id": 103,
            "title": "ent-video",
            "category": "心韓",
            "popular_count": 95,
            "publish_time": "2026-04-21T08:00:00Z",
            "post_mp4_url": "https://example.com/v.mp4",
        },
    ]
    out = generate_schedule_suggestions(
        pending_rows=pending,
        published_rows=None,
        schedule_date="2026-04-21",
        include_published_for_repost=False,
    )
    assert out["ok"] is True
    types = {row["title"]: row["suggested_post_type"] for row in out["schedule"]}
    assert types.get("social") == "text_post"
    assert types.get("ent-photo") == "photo_post"
    assert types.get("ent-video") == "video_post"


def test_conflict_requires_confirmation_then_shift_by_template():
    scheduled_items = [
        (
            datetime(2026, 4, 22, 9, 15, tzinfo=HKT_TZ),
            {
                "title": "auto-social",
                "category": "社會事",
                "post_id": 1,
                "post_link_id": "plink-1",
                "post_link_type": "text",
                "publish_time": "2026-04-22T01:15:00Z",
                "schedule_method": "auto_plugin",
                "is_locked": False,
            },
        )
    ]
    ok, msg, _, impact = _plan_publish_slot_adjustments(
        schedule_dt=datetime(2026, 4, 22, 9, 15, tzinfo=HKT_TZ),
        scheduled_items=scheduled_items,
        allow_shift=False,
        target_item={"category": "社會事"},
    )
    assert ok is False
    assert bool(impact.get("requires_confirmation")) is True

    ok2, _, pre_updates, impact2 = _plan_publish_slot_adjustments(
        schedule_dt=datetime(2026, 4, 22, 9, 15, tzinfo=HKT_TZ),
        scheduled_items=scheduled_items,
        allow_shift=True,
        target_item={"category": "社會事"},
    )
    assert ok2 is True
    assert pre_updates
    # 社會事 09:15 之后的下一个模板槽位是 09:45
    assert "01:45:00Z" in str(pre_updates[0]["post_link_time"])
    assert impact2["shifted_rows"][0]["new_time"].endswith("09:45")


@pytest.mark.skipif(
    not Path(__file__).resolve().parents[1].joinpath("data", "samples", "dashboard_pending.json").exists(),
    reason="sample file missing",
)
def test_fastapi_scheduler_generate_route_smoke():
    from fastapi.testclient import TestClient

    from src.dashboard_api.server import app

    client = TestClient(app)
    r = client.post(
        "/api/scheduler/generate",
        json={
            "schedule_date": "2026-04-21",
            "sync": False,
            "include_published_for_repost": False,
        },
    )
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        data = r.json()
        assert "schedule" in data
