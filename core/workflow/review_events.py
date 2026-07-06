# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

REVIEW_CREATED = "ReviewCreated"
REVIEW_STARTED = "ReviewStarted"
REVIEW_APPROVED = "ReviewApproved"
REVIEW_REJECTED = "ReviewRejected"
REVIEW_CHANGES_REQUESTED = "ReviewChangesRequested"
REVIEW_CANCELLED = "ReviewCancelled"


@dataclass
class ReviewEvent:
    name: str
    task_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReviewEventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[ReviewEvent], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[ReviewEvent], None]) -> None:
        self._subscribers.setdefault(event_name, []).append(callback)

    def emit(self, event: ReviewEvent) -> None:
        for callback in self._subscribers.get(event.name, []):
            callback(event)
