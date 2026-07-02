"""Event subscription registry for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .event_models import Event, EventSubscription


class EventRegistry:
    def __init__(self) -> None:
        self._subscriptions: Dict[str, EventSubscription] = {}

    def register(self, callback: Any, *, name: Optional[str] = None, topic: Optional[str] = None, event_type: Optional[str] = None, source: Optional[str] = None, priority: int = 0, metadata: Optional[Dict[str, Any]] = None) -> str:
        sub_name = name or f"subscriber-{uuid4()}"
        self._subscriptions[sub_name] = EventSubscription(name=sub_name, callback=callback, topic=topic, event_type=event_type, source=source, priority=priority, metadata=dict(metadata or {}))
        return sub_name

    def unregister(self, name: str) -> bool:
        return self._subscriptions.pop(name, None) is not None

    def enable(self, name: str) -> None:
        self._subscriptions[name].active = True

    def disable(self, name: str) -> None:
        self._subscriptions[name].active = False

    def matching(self, event: Event) -> List[EventSubscription]:
        return sorted([sub for sub in self._subscriptions.values() if sub.matches(event)], key=lambda sub: sub.priority, reverse=True)

    def manifest(self) -> Dict[str, Any]:
        return {
            "count": len(self._subscriptions),
            "subscriptions": [sub.to_dict() for sub in self._subscriptions.values()],
        }
