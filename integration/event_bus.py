"""Central Event Bus for NTPE Stage-08.5."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .event_context import EventContext
from .event_dispatcher import EventDispatcher
from .event_filters import EventFilter
from .event_models import EVENT_BUS_STAGE, EVENT_BUS_VERSION, Event, EventDispatchResult
from .event_publisher import EventPublisher
from .event_registry import EventRegistry


class EventBus:
    version = EVENT_BUS_VERSION
    stage = EVENT_BUS_STAGE

    def __init__(self, *, registry: Optional[EventRegistry] = None, context: Optional[EventContext] = None) -> None:
        self.registry = registry or EventRegistry()
        self.dispatcher = EventDispatcher(self.registry)
        self.context = context or EventContext()
        self.history: list[dict] = []

    def subscribe(self, callback: Any, *, name: Optional[str] = None, topic: Optional[str] = None, event_type: Optional[str] = None, source: Optional[str] = None, priority: int = 0, metadata: Optional[Dict[str, Any]] = None) -> str:
        return self.registry.register(callback, name=name, topic=topic, event_type=event_type, source=source, priority=priority, metadata=metadata)

    def unsubscribe(self, name: str) -> bool:
        return self.registry.unregister(name)

    def publish(self, event: Event | str, payload: Optional[Dict[str, Any]] = None, *, topic: Optional[str] = None, source: Optional[str] = None, priority: int = 0, correlation_id: Optional[str] = None, **metadata: Any) -> EventDispatchResult:
        if isinstance(event, str):
            envelope = Event(
                type=event,
                payload=dict(payload or {}),
                topic=topic or self.context.topic,
                source=source or self.context.source,
                priority=priority,
                correlation_id=correlation_id or self.context.correlation_id,
                metadata=dict(metadata),
            )
        else:
            envelope = event
        result = self.dispatcher.dispatch(envelope)
        self.history.append(result.to_dict())
        return result

    async def publish_async(self, event: Event | str, payload: Optional[Dict[str, Any]] = None, *, topic: Optional[str] = None, source: Optional[str] = None, priority: int = 0, correlation_id: Optional[str] = None, **metadata: Any) -> EventDispatchResult:
        if isinstance(event, str):
            envelope = Event(type=event, payload=dict(payload or {}), topic=topic or self.context.topic, source=source or self.context.source, priority=priority, correlation_id=correlation_id or self.context.correlation_id, metadata=dict(metadata))
        else:
            envelope = event
        result = await self.dispatcher.dispatch_async(envelope)
        self.history.append(result.to_dict())
        return result

    def publisher(self, *, source: str = "integration", topic: str = "default") -> EventPublisher:
        return EventPublisher(self, source=source, topic=topic)

    def filter_history(self, event_filter: EventFilter) -> list[dict]:
        matched = []
        for item in self.history:
            event = item.get("event", {})
            envelope = Event(
                type=event.get("type", ""),
                payload=event.get("payload", {}),
                topic=event.get("topic", "default"),
                source=event.get("source", "integration"),
                priority=event.get("priority", 0),
                correlation_id=event.get("correlation_id", ""),
                timestamp=event.get("timestamp", 0.0),
                metadata=event.get("metadata", {}),
            )
            if event_filter.match(envelope):
                matched.append(item)
        return matched

    def bridge_status(self) -> Dict[str, Any]:
        return self.context.to_dict()

    def manifest(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "foundation_status": "frozen",
            "registry": self.registry.manifest(),
            "history_count": len(self.history),
            "context": self.context.to_dict(),
        }
