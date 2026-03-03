from enum import Enum


class ReviewEvent(str, Enum):
    WAITING = "waiting"
    APPROVED = "approved"
    REJECTED = "rejected"
    TWEAK_REQUESTED = "tweak_requested"
    AUTO_APPROVED_TIMEOUT = "auto_approved_timeout"

