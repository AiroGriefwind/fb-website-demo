from __future__ import annotations

from datetime import timedelta, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = WORKSPACE_ROOT / "data" / "samples"

PUBLISHED_FILE = SAMPLES_DIR / "dashboard_published.json"
SCHEDULED_FILE = SAMPLES_DIR / "dashboard_scheduled.json"
PENDING_FILE = SAMPLES_DIR / "dashboard_pending.json"
TRENDS_FILE = SAMPLES_DIR / "google_trends_hk_mock.json"
DUMMY_THUMB_FILE = SAMPLES_DIR / "Dummy1.png"

API_BASE_URL_ENV = "DASHBOARD_API_BASE_URL"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
HKT_TZ = timezone(timedelta(hours=8))
TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=HK"
TRENDS_WEB_URL = "https://trends.google.com/trending?geo=HK"
TRENDS_RSS_TTL_SECONDS = 900
DEFAULT_SCHEDULE_WINDOW_MINUTES = 10
SCHEDULE_WINDOW_OPTIONS = [5, 10, 15, 20, 30]

CATEGORY_ORDER = ["娛樂", "社會事", "大視野", "兩岸", "法庭事", "消費", "心韓"]
CATEGORY_BASE_COLORS = {
    "社會事": "#009933",
    "大視野": "#FF6600",
    "兩岸": "#F50000",
    "法庭事": "#01143C",
    "消費": "#493692",
    "娛樂": "#990099",
    "心韓": "#9D8AD6",
}
CATEGORY_CLASS_MAP = {name: f"cat-{idx + 1}" for idx, name in enumerate(CATEGORY_ORDER)}
CATEGORY_INTENSITY_OVERRIDES = {
    "法庭事": {"header": 0.44, "border": 0.58, "card": 0.34},
    "消費": {"header": 0.44, "border": 0.58, "card": 0.34},
    "心韓": {"header": 0.40, "border": 0.54, "card": 0.30},
}
