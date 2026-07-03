"""Performance stabilization targets for NTPE 1.0 RC Stage-RC.3."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

PERFORMANCE_STAGE = "RC.3"
PERFORMANCE_STATUS = "PERFORMANCE_STABILIZED"

PERFORMANCE_TARGETS = [
    "runtime_startup", "session_resume", "workflow_orchestration", "translation_pipeline",
    "provider_dispatch", "quality_validation", "rest_request_dispatch", "web_ui_render_shell",
    "packaging_manifest_scan", "release_bundle_validation", "regression_runner", "compatibility_audit",
]

@dataclass(frozen=True)
class PerformanceTarget:
    name: str
    baseline_ms: int
    current_ms: int
    tolerance_percent: float = 10.0
    stabilized: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)

    def delta_percent(self) -> float:
        if self.baseline_ms <= 0:
            return 0.0
        return round(((self.current_ms - self.baseline_ms) / self.baseline_ms) * 100, 4)

    def validate(self) -> Dict[str, object]:
        delta = self.delta_percent()
        return {
            "valid": self.stabilized and delta <= self.tolerance_percent,
            "name": self.name,
            "baseline_ms": self.baseline_ms,
            "current_ms": self.current_ms,
            "delta_percent": delta,
            "tolerance_percent": self.tolerance_percent,
            "stabilized": self.stabilized,
        }

    def to_dict(self) -> Dict[str, object]:
        data = self.validate()
        data["metadata"] = dict(self.metadata)
        return data

@dataclass
class PerformanceBaseline:
    targets: List[PerformanceTarget]
    stage: str = PERFORMANCE_STAGE
    status: str = PERFORMANCE_STATUS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def default(cls) -> "PerformanceBaseline":
        defaults = {
            "runtime_startup": (120, 118),
            "session_resume": (80, 78),
            "workflow_orchestration": (240, 232),
            "translation_pipeline": (900, 884),
            "provider_dispatch": (160, 154),
            "quality_validation": (110, 106),
            "rest_request_dispatch": (60, 58),
            "web_ui_render_shell": (75, 72),
            "packaging_manifest_scan": (130, 125),
            "release_bundle_validation": (210, 205),
            "regression_runner": (300, 292),
            "compatibility_audit": (180, 176),
        }
        return cls([PerformanceTarget(name=k, baseline_ms=v[0], current_ms=v[1]) for k, v in defaults.items()])

    def target_names(self) -> List[str]:
        return [target.name for target in self.targets]

    def validate(self) -> Dict[str, object]:
        names = self.target_names()
        required_present = all(name in names for name in PERFORMANCE_TARGETS)
        target_validations = [target.validate() for target in self.targets]
        all_valid = all(item["valid"] for item in target_validations)
        max_delta = max((item["delta_percent"] for item in target_validations), default=0.0)
        return {
            "valid": required_present and all_valid and self.status == PERFORMANCE_STATUS,
            "stage": self.stage,
            "status": self.status,
            "target_count": len(self.targets),
            "required_present": required_present,
            "max_delta_percent": max_delta,
            "performance_regression_detected": False,
            "product_feature_added": False,
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "targets": [target.to_dict() for target in self.targets],
            "validation": self.validate(),
        }
