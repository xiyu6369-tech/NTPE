"""Pipeline page models for NTPE Stage-13.5 Web UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

WEB_UI_PIPELINE_STAGE = "13.5"


@dataclass(frozen=True)
class PipelineAction:
    """Declarative UI action for pipeline operations exposed through REST."""

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
class PipelinePageView:
    """Framework-neutral pipeline page view model."""

    pipelines: List[Dict[str, Any]]
    actions: List[PipelineAction]
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = WEB_UI_PIPELINE_STAGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "pipelines": [dict(pipeline) for pipeline in self.pipelines],
            "actions": [action.to_dict() for action in self.actions],
            "metadata": dict(self.metadata),
        }
