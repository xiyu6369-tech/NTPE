"""Event page models for NTPE Stage-13.6 Web UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

WEB_UI_EVENT_STAGE = "13.6"


@dataclass(frozen=True)
class EventAction:
    """Declarative UI action for event operations exposed through REST."""

    action_id: str
    label: str
    method: str
    path_template: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "method": self.method,
            "path_template": self.path_template,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EventPageView:
    """Framework-neutral event page view model."""

    events: List[Dict[str, Any]]
    actions: List[EventAction]
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = WEB_UI_EVENT_STAGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "events": [dict(event) for event in self.events],
            "actions": [action.to_dict() for action in self.actions],
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
        }
