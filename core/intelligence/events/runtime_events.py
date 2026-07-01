"""Foundation-07.5 standard intelligence event names and facade."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .event import IntelligenceEvent
from .event_bus import IntelligenceEventBus
from .publisher import IntelligencePublisher

SEGMENT_STARTED = "SegmentStarted"
SEGMENT_COMPLETED = "SegmentCompleted"
SNAPSHOT_CREATED = "SnapshotCreated"
SNAPSHOT_UPDATED = "SnapshotUpdated"
CHARACTER_UPDATED = "CharacterUpdated"
GLOSSARY_MATCHED = "GlossaryMatched"
NARRATIVE_UPDATED = "NarrativeUpdated"
SCENE_UPDATED = "SceneUpdated"
CONSISTENCY_CHECKED = "ConsistencyChecked"
RUNTIME_PERSISTED = "RuntimePersisted"

STANDARD_INTELLIGENCE_EVENTS = [
    SEGMENT_STARTED,
    SEGMENT_COMPLETED,
    SNAPSHOT_CREATED,
    SNAPSHOT_UPDATED,
    CHARACTER_UPDATED,
    GLOSSARY_MATCHED,
    NARRATIVE_UPDATED,
    SCENE_UPDATED,
    CONSISTENCY_CHECKED,
    RUNTIME_PERSISTED,
]


class IntelligenceRuntimeEventFacade:
    """Typed event facade used by runtime/lifecycle/persistence integration tests."""

    version = "foundation-07.5"

    def __init__(self, bus: Optional[IntelligenceEventBus] = None) -> None:
        self.bus = bus or IntelligenceEventBus()
        self.runtime = IntelligencePublisher(self.bus, source="runtime")
        self.lifecycle = IntelligencePublisher(self.bus, source="lifecycle")
        self.persistence = IntelligencePublisher(self.bus, source="persistence")

    def segment_started(self, segment_id: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.runtime.publish(SEGMENT_STARTED, payload=payload or {}, segment_id=segment_id)

    def segment_completed(self, segment_id: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.runtime.publish(SEGMENT_COMPLETED, payload=payload or {}, segment_id=segment_id)

    def snapshot_created(self, scope_key: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.lifecycle.publish(SNAPSHOT_CREATED, payload=payload or {}, scope_key=scope_key)

    def snapshot_updated(self, scope_key: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.lifecycle.publish(SNAPSHOT_UPDATED, payload=payload or {}, scope_key=scope_key)

    def consistency_checked(self, segment_id: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.runtime.publish(CONSISTENCY_CHECKED, payload=payload or {}, segment_id=segment_id)

    def runtime_persisted(self, scope_key: str, payload: Optional[Dict[str, Any]] = None) -> IntelligenceEvent:
        return self.persistence.publish(RUNTIME_PERSISTED, payload=payload or {}, scope_key=scope_key)
