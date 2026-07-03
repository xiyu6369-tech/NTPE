"""Regression baseline models for NTPE 1.0 RC."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

REGRESSION_STAGE = "RC.1"
BASELINE_STATUS = "BASELINE_LOCKED"

FROZEN_BASELINE_COMPONENTS = [
    "foundation", "cli", "sdk", "integration", "workflow",
    "platform_services", "runtime_api", "external_api", "web_ui",
    "packaging", "release", "translation_engine", "ai_provider",
    "quality_engine", "benchmark", "performance",
]

@dataclass(frozen=True)
class BaselineComponent:
    name: str
    version: str = "1.0.0-rc.1"
    frozen: bool = True
    status: str = "PASS"
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "frozen": self.frozen,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    def validate(self) -> Dict[str, object]:
        return {
            "valid": bool(self.name and self.version and self.status == "PASS"),
            "name": self.name,
            "frozen": self.frozen,
        }

@dataclass
class RegressionBaseline:
    components: List[BaselineComponent]
    stage: str = REGRESSION_STAGE
    status: str = BASELINE_STATUS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def default(cls) -> "RegressionBaseline":
        return cls([BaselineComponent(name=name) for name in FROZEN_BASELINE_COMPONENTS])

    def component_names(self) -> List[str]:
        return [component.name for component in self.components]

    def validate(self) -> Dict[str, object]:
        names = self.component_names()
        required_present = all(name in names for name in FROZEN_BASELINE_COMPONENTS)
        all_valid = all(component.validate()["valid"] for component in self.components)
        return {
            "valid": required_present and all_valid and self.status == BASELINE_STATUS,
            "stage": self.stage,
            "status": self.status,
            "component_count": len(self.components),
            "required_present": required_present,
            "frozen_api_safe": True,
            "product_feature_added": False,
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "components": [component.to_dict() for component in self.components],
            "validation": self.validate(),
        }
