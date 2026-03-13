from __future__ import annotations

import json
import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from xml.etree import ElementTree as ET

import streamlit as st

from src.dashboard.config import (
    API_BASE_URL_ENV,
    HKT_TZ,
    PENDING_FILE,
    PUBLISHED_FILE,
    SCHEDULED_FILE,
    TRENDS_FILE,
    TRENDS_RSS_TTL_SECONDS,
    TRENDS_RSS_URL,
)


def read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    return []


def write_json_list(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_from_api(dataset: str) -> list[dict[str, Any]] | None:
    base_url = os.getenv(API_BASE_URL_ENV, "").strip()
    if not base_url:
        return None

    url = f"{base_url.rstrip('/')}/{dataset.lstrip('/')}"
    try:
        with urllib_request.urlopen(url, timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if isinstance(payload, list):
            return payload
    except (OSError, ValueError, urllib_error.URLError):
        return None
    return None


def load_dataset(dataset: str, fallback_path: Path) -> list[dict[str, Any]]:
    api_data = load_from_api(dataset)
    if api_data is not None:
        return api_data
    return read_json_list(fallback_path)


def load_published_items() -> list[dict[str, Any]]:
    return load_dataset("published", PUBLISHED_FILE)


def load_scheduled_items() -> list[dict[str, Any]]:
    return load_dataset("scheduled", SCHEDULED_FILE)


def load_pending_base() -> list[dict[str, Any]]:
    return load_dataset("pending", PENDING_FILE)


def load_trending_keywords() -> list[dict[str, Any]]:
    rss_data = load_trending_keywords_from_rss()
    if rss_data:
        return rss_data
    return load_dataset("trends", TRENDS_FILE)


@st.cache_data(show_spinner=False, ttl=TRENDS_RSS_TTL_SECONDS)
def load_trending_keywords_from_rss() -> list[dict[str, Any]]:
    try:
        with urllib_request.urlopen(TRENDS_RSS_URL, timeout=8) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")
    except (OSError, urllib_error.URLError):
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    ns = {"ht": "https://trends.google.com/trending/rss"}
    data: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        keyword = (item.findtext("title") or "").strip()
        traffic = (item.findtext("ht:approx_traffic", namespaces=ns) or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        detail_items: list[dict[str, str]] = []
        for news in item.findall("ht:news_item", namespaces=ns):
            news_title = (news.findtext("ht:news_item_title", namespaces=ns) or "").strip()
            news_url = (news.findtext("ht:news_item_url", namespaces=ns) or "").strip()
            news_source = (news.findtext("ht:news_item_source", namespaces=ns) or "").strip()
            if news_title:
                detail_items.append({"title": news_title, "url": news_url, "source": news_source})
        pub_date = pub_date_raw
        if pub_date_raw:
            try:
                dt = parsedate_to_datetime(pub_date_raw).astimezone(HKT_TZ)
                pub_date = dt.strftime("%m/%d %H:%M")
                pub_ts = int(dt.timestamp())
            except (TypeError, ValueError, OSError):
                pub_date = pub_date_raw
                pub_ts = 0
        else:
            pub_ts = 0
        if keyword:
            data.append(
                {
                    "keyword": keyword,
                    "search_volume": traffic or "N/A",
                    "published_at": pub_date,
                    "published_ts": pub_ts,
                    "source": "rss",
                    "detail_items": detail_items,
                }
            )
    return data[:20]


def persist_trending_keywords(data: list[dict[str, Any]]) -> None:
    TRENDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def traffic_to_int(value: str) -> int:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else 0


def published_to_sort_ts(item: dict[str, Any]) -> int:
    raw_ts = int(item.get("published_ts") or 0)
    if raw_ts > 0:
        return raw_ts
    raw = str(item.get("published_at", "")).strip()
    if not raw:
        return 0
    try:
        dt = datetime.strptime(raw, "%m/%d %H:%M").replace(year=datetime.now(HKT_TZ).year, tzinfo=HKT_TZ)
        return int(dt.timestamp())
    except ValueError:
        return 0
