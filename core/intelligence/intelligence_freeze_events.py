# =====================================================
# NTPE 1.2 Professional
# Stage-16.8 Advanced Translation Intelligence Freeze
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


INTELLIGENCE_FREEZE_STARTED = "IntelligenceFreezeStarted"
INTELLIGENCE_FREEZE_VALIDATED = "IntelligenceFreezeValidated"
INTELLIGENCE_FREEZE_COMPLETED = "IntelligenceFreezeCompleted"


@dataclass(frozen=True)
class IntelligenceFreezeEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class IntelligenceFreezeEventBus:
    """Small in-process event bus for freeze validation diagnostics."""

    def __init__(self) -> None:
        self.events: List[IntelligenceFreezeEvent] = []

    def emit(self, name: str, **payload: Any) -> IntelligenceFreezeEvent:
        event = IntelligenceFreezeEvent(name=name, payload=dict(payload))
        self.events.append(event)
        return event
