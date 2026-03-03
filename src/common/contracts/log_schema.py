from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.common.contracts.task_status import TaskStage, TaskState


@dataclass
class TaskLogRecord:
    run_id: str
    stage: TaskStage
    state: TaskState
    message: str
    retry_count: int = 0
    error_code: Optional[str] = None
    error_detail: Optional[str] = None
    created_at: str = datetime.now(timezone.utc).isoformat()
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload.get("metadata") is None:
            payload["metadata"] = {}
        return payload

