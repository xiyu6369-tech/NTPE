"""Event dispatcher for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

import inspect
from typing import List

from .event_models import Event, EventDispatchResult
from .event_registry import EventRegistry


class EventDispatcher:
    def __init__(self, registry: EventRegistry) -> None:
        self.registry = registry

    def dispatch(self, event: Event) -> EventDispatchResult:
        delivered = 0
        errors: List[str] = []
        for subscription in self.registry.matching(event):
            try:
                subscription.callback(event)
                delivered += 1
            except Exception as exc:  # pragma: no cover - defensive boundary
                errors.append(f"{subscription.name}: {exc}")
        return EventDispatchResult(ok=not errors, event=event, delivered=delivered, errors=errors)

    async def dispatch_async(self, event: Event) -> EventDispatchResult:
        delivered = 0
        errors: List[str] = []
        for subscription in self.registry.matching(event):
            try:
                result = subscription.callback(event)
                if inspect.isawaitable(result):
                    await result
                delivered += 1
            except Exception as exc:  # pragma: no cover - defensive boundary
                errors.append(f"{subscription.name}: {exc}")
        return EventDispatchResult(ok=not errors, event=event, delivered=delivered, errors=errors)
