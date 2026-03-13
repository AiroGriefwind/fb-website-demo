from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from src.dashboard.config import DUMMY_THUMB_FILE, HKT_TZ, WORKSPACE_ROOT


@st.cache_data(show_spinner=False)
def file_to_data_uri(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists() or not path.is_file():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def resolve_thumbnail_src(raw_thumbnail: str) -> str:
    raw = (raw_thumbnail or "").strip()
    if raw.startswith(("http://", "https://", "data:")):
        return raw

    if raw:
        raw_path = Path(raw)
        if not raw_path.is_absolute():
            raw_path = WORKSPACE_ROOT / raw_path
        data_uri = file_to_data_uri(str(raw_path))
        if data_uri:
            return data_uri

    return file_to_data_uri(str(DUMMY_THUMB_FILE))


def parse_publish_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(HKT_TZ)
    except ValueError:
        return None


def round_up_to_5_minutes(dt: datetime) -> datetime:
    next_mark = ((dt.minute + 4) // 5) * 5
    if next_mark >= 60:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(minute=next_mark, second=0, microsecond=0)
    return dt


def to_utc_iso_z(dt_hkt: datetime) -> str:
    return dt_hkt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
