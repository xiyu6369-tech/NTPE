"""Foundation-07.5 in-process Intelligence Event Bus."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Optional, Union

from .event import IntelligenceEvent

EventLike = Union[IntelligenceEvent, Dict[str, Any], str]
EventHandler = Callable[[IntelligenceEvent], Any]


class IntelligenceEventBus:
    """Small synchronous event bus for Intelligence Runtime/Lifecycle/Persistence.

    The bus is dependency-free and intentionally in-process. It supports exact event
    subscriptions and wildcard subscriptions via ``*`` for observability tests and
    future adapters.
    """

    version = "foundation-07.5"

    def __init__(self, keep_history: bool = True, max_history: int = 1000) -> None:
        self.keep_history = keep_history
        self.max_history = max(1, int(max_history))
        self._subscribers: DefaultDict[str, List[EventHandler]] = defaultdict(list)
        self._history: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> EventHandler:
        event_name = str(event_type or "*")
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
        return handler

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        event_name = str(event_type or "*")
        handlers = self._subscribers.get(event_name, [])
        if handler not in handlers:
            return False
        handlers.remove(handler)
        return True

    def publish(
        self,
        event: EventLike,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> IntelligenceEvent:
        built = self._coerce_event(event, payload=payload, **kwargs)
        if self.keep_history:
            self._history.append(built.to_dict())
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history :]

        for handler in self._iter_handlers(built.event_type):
            handler(built)
        return built

    def history(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        items = deepcopy(self._history)
        if event_type is None:
            return items
        return [item for item in items if item.get("event_type") == event_type]

    def clear_history(self) -> None:
        self._history.clear()

    def subscriber_count(self, event_type: Optional[str] = None) -> int:
        if event_type is not None:
            return len(self._subscribers.get(str(event_type), []))
        return sum(len(items) for items in self._subscribers.values())

    def _iter_handlers(self, event_type: str) -> Iterable[EventHandler]:
        yielded: List[EventHandler] = []
        for name in (event_type, "*"):
            for handler in list(self._subscribers.get(name, [])):
                if handler not in yielded:
                    yielded.append(handler)
                    yield handler

    def _coerce_event(
        self,
        event: EventLike,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> IntelligenceEvent:
        if isinstance(event, IntelligenceEvent):
            return event
        if isinstance(event, dict):
            data = dict(event)
            if payload:
                merged = dict(data.get("payload") or {})
                merged.update(payload)
                data["payload"] = merged
            data.update({k: v for k, v in kwargs.items() if v is not None})
            return IntelligenceEvent.from_dict(data)
        return IntelligenceEvent(event_type=str(event), payload=dict(payload or {}), **kwargs)
