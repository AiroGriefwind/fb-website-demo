"""Add views, engagements, top_ranking, ai_ranking, social_media_share to board sample JSON rows.

Only 娛樂 / 心韓 get non-zero views & engagements; others are 0.
Run from repo root: python scripts/annotate_board_metrics.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "data" / "samples" / "dashboard_pending.json",
    ROOT / "data" / "samples" / "dashboard_published.json",
    ROOT / "data" / "samples" / "dashboard_scheduled.json",
]


def enrich(item: dict, global_i: int) -> None:
    cat = str(item.get("category", ""))
    ent = cat in ("娛樂", "心韓")
    sid = str(item.get("item_id", global_i))
    h = sum(ord(c) for c in sid) % 997

    if ent:
        item["views"] = 2000 + (h * 97) % 48000
        item["engagements"] = 100 + (h * 31) % 8000
    else:
        item["views"] = 0
        item["engagements"] = 0

    item["top_ranking"] = h % 6
    item["ai_ranking"] = (h * 3) % 6
    item["social_media_share"] = bool(h % 3 == 0)


def main() -> None:
    g = 0
    for fp in FILES:
        if not fp.exists():
            print("skip (missing):", fp)
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print("skip (not list):", fp)
            continue
        for item in data:
            if isinstance(item, dict):
                enrich(item, g)
                g += 1
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("updated", fp.name, "rows", len(data))


if __name__ == "__main__":
    main()
