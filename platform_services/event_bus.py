"""Platform event bus for NTPE 1.0 Beta Stage-10.5.

The event bus is an additive Platform Services layer. It is intentionally
in-memory and dependency-free so it does not mutate frozen Foundation, CLI,
SDK, Integration, or Workflow behavior.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatch
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Optional
from uuid import uuid4

PLATFORM_EVENT_BUS_VERSION = "1.0.0-beta.10.5"
PLATFORM_EVENT_BUS_STAGE = "10.5"

EventHandler = Callable[["PlatformEvent"], Any]


@dataclass(frozen=True)
class PlatformEvent:
    """Immutable event payload used by PlatformEventBus."""

    event_type: str
    payload: Any = None
    source: str = "platform"
    topic: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"platform-event-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.event_type or not str(self.event_type).strip():
            raise ValueError("event_type is required")
        object.__setattr__(self, "event_type", str(self.event_type))
        object.__setattr__(self, "source", str(self.source or "platform"))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.topic is not None:
            object.__setattr__(self, "topic", str(self.topic))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "topic": self.topic,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class PlatformEventDelivery:
    """Result produced when dispatching one event to one subscriber."""

    event_id: str
    subscriber_id: str
    ok: bool
    value: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "subscriber_id": self.subscriber_id,
            "ok": self.ok,
            "value": self.value,
            "error": self.error,
        }


@dataclass
class PlatformEventSubscription:
    """Subscription descriptor for exact or wildcard event patterns."""

    pattern: str
    handler: EventHandler
    subscriber_id: str = field(default_factory=lambda: f"platform-subscriber-{uuid4().hex[:12]}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def __post_init__(self) -> None:
        if not self.pattern or not str(self.pattern).strip():
            raise ValueError("subscription pattern is required")
        if not callable(self.handler):
            raise TypeError("subscription handler must be callable")
        self.pattern = str(self.pattern)
        self.metadata = dict(self.metadata or {})

    def matches(self, event_type: str) -> bool:
        return self.active and fnmatch(str(event_type), self.pattern)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscriber_id": self.subscriber_id,
            "pattern": self.pattern,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


class PlatformEventBus:
    """Synchronous in-memory event bus for Platform Services."""

    version = PLATFORM_EVENT_BUS_VERSION
    stage = PLATFORM_EVENT_BUS_STAGE

    def __init__(self, *, retain_history: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.retain_history = bool(retain_history)
        self.metadata = dict(metadata or {})
        self._subscriptions: DefaultDict[str, List[PlatformEventSubscription]] = defaultdict(list)
        self._history: List[PlatformEvent] = []
        self._deliveries: List[PlatformEventDelivery] = []

    def subscribe(self, pattern: str, handler: EventHandler, *, metadata: Optional[Dict[str, Any]] = None) -> PlatformEventSubscription:
        subscription = PlatformEventSubscription(pattern=str(pattern), handler=handler, metadata=dict(metadata or {}))
        self._subscriptions[subscription.pattern].append(subscription)
        return subscription

    def unsubscribe(self, subscriber_id: str) -> bool:
        found = False
        for subscriptions in self._subscriptions.values():
            for subscription in subscriptions:
                if subscription.subscriber_id == subscriber_id:
                    subscription.active = False
                    found = True
        return found

    def publish(
        self,
        event_type: str,
        payload: Any = None,
        *,
        source: str = "platform",
        topic: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PlatformEvent:
        event = PlatformEvent(event_type, payload=payload, source=source, topic=topic, metadata=dict(metadata or {}))
        if self.retain_history:
            self._history.append(event)
        self.dispatch(event)
        return event

    def dispatch(self, event: PlatformEvent) -> List[PlatformEventDelivery]:
        deliveries: List[PlatformEventDelivery] = []
        for subscription in self.subscriptions_for(event.event_type):
            try:
                value = subscription.handler(event)
                delivery = PlatformEventDelivery(event.event_id, subscription.subscriber_id, True, value=value)
            except Exception as exc:  # intentionally captures handler failure per subscriber
                delivery = PlatformEventDelivery(event.event_id, subscription.subscriber_id, False, error=str(exc))
            deliveries.append(delivery)
            self._deliveries.append(delivery)
        return deliveries

    def subscriptions_for(self, event_type: str) -> List[PlatformEventSubscription]:
        matched: List[PlatformEventSubscription] = []
        for subscriptions in self._subscriptions.values():
            for subscription in subscriptions:
                if subscription.matches(event_type):
                    matched.append(subscription)
        return matched

    def history(self, *, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[PlatformEvent]:
        events: Iterable[PlatformEvent] = self._history
        if event_type is not None:
            events = [event for event in events if event.event_type == event_type]
        result = list(events)
        if limit is not None:
            result = result[-int(limit):]
        return result

    def deliveries(self, *, event_id: Optional[str] = None) -> List[PlatformEventDelivery]:
        if event_id is None:
            return list(self._deliveries)
        return [delivery for delivery in self._deliveries if delivery.event_id == event_id]

    def summary(self) -> Dict[str, Any]:
        subscriptions = [subscription for items in self._subscriptions.values() for subscription in items]
        return {
            "version": self.version,
            "stage": self.stage,
            "event_count": len(self._history),
            "subscription_count": len(subscriptions),
            "active_subscription_count": sum(1 for subscription in subscriptions if subscription.active),
            "delivery_count": len(self._deliveries),
            "failed_delivery_count": sum(1 for delivery in self._deliveries if not delivery.ok),
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "foundation_status": "frozen",
            "cli_status": "frozen",
            "sdk_status": "complete",
            "integration_status": "frozen",
            "workflow_status": "frozen",
            "additive_only": True,
            "subscriptions": [subscription.to_dict() for items in self._subscriptions.values() for subscription in items],
            "metadata": dict(self.metadata),
        }


def create_event_bus(**kwargs: Any) -> PlatformEventBus:
    return PlatformEventBus(**kwargs)
