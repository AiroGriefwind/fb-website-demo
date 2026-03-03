from enum import Enum


class TaskStage(str, Enum):
    SCRAPE = "scrape"
    SCORE = "score"
    SCHEDULE = "schedule"
    REVIEW = "review"
    DISPATCH = "dispatch"
    ARCHIVE = "archive"


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_HUMAN = "needs_human"
    CANCELLED = "cancelled"

