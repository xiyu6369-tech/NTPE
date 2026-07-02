"""Session page models for NTPE Stage-13.3 Web UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

WEB_UI_SESSION_STAGE = "13.3"


@dataclass(frozen=True)
class SessionAction:
    """Declarative UI action for session operations exposed through REST."""

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
class SessionPageView:
    """Framework-neutral session page view model."""

    sessions: List[Dict[str, Any]]
    actions: List[SessionAction]
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = WEB_UI_SESSION_STAGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "sessions": [dict(session) for session in self.sessions],
            "actions": [action.to_dict() for action in self.actions],
            "metadata": dict(self.metadata),
        }
