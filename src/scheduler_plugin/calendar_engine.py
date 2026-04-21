from __future__ import annotations

import holidays
from datetime import date

from src.scheduler_plugin.schedule_config import WEEKEND_SCHEDULE, WORKDAY_SCHEDULE

hk_holidays = holidays.HK()


def is_weekend(check_date: date) -> bool:
    return check_date.weekday() >= 5


def is_holiday(check_date: date) -> bool:
    return check_date in hk_holidays


def is_weekend_or_holiday(check_date: date) -> bool:
    return is_weekend(check_date) or is_holiday(check_date)


def get_day_type(check_date: date) -> str:
    if is_weekend_or_holiday(check_date):
        return "weekend"
    return "workday"


def get_schedule_for_date(check_date: date):
    day_type = get_day_type(check_date)
    schedule = WORKDAY_SCHEDULE.copy() if day_type == "workday" else WEEKEND_SCHEDULE.copy()
    for slot in schedule:
        if slot.get("mode") == "manual":
            slot["mode"] = "auto"
    return schedule
