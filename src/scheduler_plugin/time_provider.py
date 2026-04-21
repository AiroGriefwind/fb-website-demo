from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

HK_TZ = ZoneInfo("Asia/Hong_Kong")


class TimeProvider:
    def now(self) -> datetime:
        fake_now = os.getenv("FAKE_NOW", "").strip()
        if fake_now:
            return datetime.fromisoformat(fake_now).replace(tzinfo=HK_TZ)
        return datetime.now(HK_TZ)
