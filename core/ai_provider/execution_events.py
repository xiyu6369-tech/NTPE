from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, DefaultDict, Dict, Iterable, List
from collections import defaultdict


EXECUTION_STARTED = "execution.started"
EXECUTION_RETRY = "execution.retry"
EXECUTION_TIMEOUT = "execution.timeout"
EXECUTION_COMPLETED = "execution.completed"
EXECUTION_CANCELLED = "execution.cancelled"
EXECUTION_FAILED = "execution.failed"


@dataclass(frozen=True)
class ExecutionEvent:
    name: str
    provider: str | None = None
    payload: Dict[str, Any] = field(default_factory=dict)


class ExecutionEventBus:
    def __init__(self):
        self._subscribers: DefaultDict[str, List[Callable[[ExecutionEvent], None]]] = defaultdict(list)
        self.history: List[ExecutionEvent] = []

    def subscribe(self, name: str, callback: Callable[[ExecutionEvent], None]) -> None:
        self._subscribers[name].append(callback)

    def publish(self, event: ExecutionEvent) -> None:
        self.history.append(event)
        for callback in list(self._subscribers.get(event.name, [])):
            callback(event)
        for callback in list(self._subscribers.get("*", [])):
            callback(event)

    def names(self) -> Iterable[str]:
        return self._subscribers.keys()
