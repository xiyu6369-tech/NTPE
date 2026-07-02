"""Job page models for NTPE Stage-13.4 Web UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

WEB_UI_JOB_STAGE = "13.4"


@dataclass(frozen=True)
class JobAction:
    """Declarative UI action for job operations exposed through REST."""

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
class JobPageView:
    """Framework-neutral job page view model."""

    jobs: List[Dict[str, Any]]
    actions: List[JobAction]
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = WEB_UI_JOB_STAGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "jobs": [dict(job) for job in self.jobs],
            "actions": [action.to_dict() for action in self.actions],
            "metadata": dict(self.metadata),
        }
