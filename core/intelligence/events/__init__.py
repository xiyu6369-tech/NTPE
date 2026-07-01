"""Foundation-07.5 Intelligence Event Bus public API."""

from .dispatcher import IntelligenceEventDispatcher
from .event import IntelligenceEvent
from .event_bus import IntelligenceEventBus
from .publisher import IntelligencePublisher
from .runtime_events import (
    CHARACTER_UPDATED,
    CONSISTENCY_CHECKED,
    GLOSSARY_MATCHED,
    NARRATIVE_UPDATED,
    RUNTIME_PERSISTED,
    SCENE_UPDATED,
    SEGMENT_COMPLETED,
    SEGMENT_STARTED,
    SNAPSHOT_CREATED,
    SNAPSHOT_UPDATED,
    STANDARD_INTELLIGENCE_EVENTS,
    IntelligenceRuntimeEventFacade,
)
from .subscriber import IntelligenceSubscriber

__all__ = [
    "CHARACTER_UPDATED",
    "CONSISTENCY_CHECKED",
    "GLOSSARY_MATCHED",
    "IntelligenceEvent",
    "IntelligenceEventBus",
    "IntelligenceEventDispatcher",
    "IntelligencePublisher",
    "IntelligenceRuntimeEventFacade",
    "IntelligenceSubscriber",
    "NARRATIVE_UPDATED",
    "RUNTIME_PERSISTED",
    "SCENE_UPDATED",
    "SEGMENT_COMPLETED",
    "SEGMENT_STARTED",
    "SNAPSHOT_CREATED",
    "SNAPSHOT_UPDATED",
    "STANDARD_INTELLIGENCE_EVENTS",
]
