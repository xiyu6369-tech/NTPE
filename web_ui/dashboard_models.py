"""Dashboard model primitives for NTPE 1.0 Beta Stage-13.2.

The dashboard layer is framework-neutral and consumes only WebUiState data
provided by the Web UI REST client. It does not call runtime internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .ui_models import utc_now_iso

WEB_UI_DASHBOARD_STAGE = "13.2"


@dataclass(frozen=True)
class DashboardMetric:
    """Serializable dashboard metric card."""

    key: str
    label: str
    value: Any
    status: str = "normal"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", str(self.key or "metric"))
        object.__setattr__(self, "label", str(self.label or self.key))
        object.__setattr__(self, "status", str(self.status or "normal").lower())
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DashboardSection:
    """A renderable dashboard section."""

    section_id: str
    title: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "section_id", str(self.section_id or "section"))
        object.__setattr__(self, "title", str(self.title or self.section_id))
        object.__setattr__(self, "items", [dict(item) for item in (self.items or [])])
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "items": [dict(item) for item in self.items],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DashboardView:
    """Complete dashboard render model."""

    metrics: List[DashboardMetric] = field(default_factory=list)
    sections: List[DashboardSection] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": WEB_UI_DASHBOARD_STAGE,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "sections": [section.to_dict() for section in self.sections],
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }
