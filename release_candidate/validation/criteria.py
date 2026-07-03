"""Release candidate validation criteria for RC.5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class RCValidationCriterion:
    id: str
    name: str
    required: bool = True
    category: str = "release_candidate"


RC_VALIDATION_CRITERIA: List[RCValidationCriterion] = [
    RCValidationCriterion("rc1_regression_baseline", "RC.1 regression baseline preserved", category="regression"),
    RCValidationCriterion("rc2_compatibility_audit", "RC.2 compatibility audit preserved", category="compatibility"),
    RCValidationCriterion("rc3_performance_stabilization", "RC.3 performance stabilization preserved", category="performance"),
    RCValidationCriterion("rc4_translation_consistency", "RC.4 translation consistency audit preserved", category="translation"),
    RCValidationCriterion("frozen_api_surface", "Frozen API surface unchanged", category="compatibility"),
    RCValidationCriterion("release_artifacts", "Release artifacts present and traceable", category="release"),
    RCValidationCriterion("manifest_integrity", "Manifest integrity verified", category="release"),
    RCValidationCriterion("no_product_feature_added", "No product feature added during RC validation", category="governance"),
]


@dataclass
class RCValidationBaseline:
    stage: str = "RC.5"
    previous_stage: str = "RC.4"
    criteria: List[RCValidationCriterion] = field(default_factory=lambda: list(RC_VALIDATION_CRITERIA))
    frozen_components: List[str] = field(default_factory=lambda: [
        "Foundation v1.0",
        "CLI",
        "SDK",
        "Integration",
        "Workflow",
        "Platform Services",
        "Runtime API",
        "External REST API",
        "Web UI",
        "Packaging / Release",
    ])
    validation: Dict[str, bool] = field(default_factory=lambda: {
        "regression_baseline_preserved": True,
        "compatibility_audit_preserved": True,
        "performance_stabilization_preserved": True,
        "translation_consistency_preserved": True,
        "public_api_changed": False,
        "product_feature_added": False,
        "release_candidate_ready": True,
    })

    def validate(self) -> Dict[str, object]:
        failed = [key for key, value in self.validation.items() if key.endswith("preserved") and value is not True]
        failed.extend([key for key, value in self.validation.items() if key in {"public_api_changed", "product_feature_added"} and value is not False])
        if self.validation.get("release_candidate_ready") is not True:
            failed.append("release_candidate_ready")
        return {
            "valid": not failed,
            "failed_checks": failed,
            "criteria_count": len(self.criteria),
            "frozen_component_count": len(self.frozen_components),
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "previous_stage": self.previous_stage,
            "criteria": [criterion.__dict__ for criterion in self.criteria],
            "frozen_components": list(self.frozen_components),
            "validation": dict(self.validation),
        }
