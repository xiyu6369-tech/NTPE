"""Resource page models for NTPE Stage-13.7 Web UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

WEB_UI_RESOURCE_STAGE = "13.7"


@dataclass(frozen=True)
class ResourceAction:
    """Declarative UI action for resource operations exposed through REST."""

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
class ResourcePageView:
    """Framework-neutral resource page view model."""

    resources: List[Dict[str, Any]]
    actions: List[ResourceAction]
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = WEB_UI_RESOURCE_STAGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "resources": [dict(resource) for resource in self.resources],
            "actions": [action.to_dict() for action in self.actions],
            "summary": dict(self.summary),
            "metadata": dict(self.metadata),
        }
