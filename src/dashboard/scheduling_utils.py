from __future__ import annotations

import os
from datetime import datetime, timezone

from src.dashboard.config import API_BASE_URL_ENV, PENDING_FILE, SCHEDULED_FILE
from src.dashboard.data_utils import read_json_list, write_json_list
from src.dashboard.media_utils import to_utc_iso_z


def move_pending_item_to_scheduled(item_id: str, schedule_hkt: datetime) -> tuple[bool, str]:
    if os.getenv(API_BASE_URL_ENV, "").strip():
        return False, "当前为 API 数据源模式，已禁用本地样本写入。"

    pending_rows = read_json_list(PENDING_FILE)
    scheduled_rows = read_json_list(SCHEDULED_FILE)
    target_idx = next((idx for idx, row in enumerate(pending_rows) if str(row.get("item_id", "")) == item_id), -1)
    if target_idx < 0:
        return False, "未找到目标待排程贴文，可能已被其他操作处理。"

    row = pending_rows.pop(target_idx)
    row["publish_time"] = to_utc_iso_z(schedule_hkt)
    row["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    row["review_status"] = "scheduled"
    scheduled_rows.append(row)

    write_json_list(PENDING_FILE, pending_rows)
    write_json_list(SCHEDULED_FILE, scheduled_rows)
    return True, "已完成排程并更新本地样本数据。"
