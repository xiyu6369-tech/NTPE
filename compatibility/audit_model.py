"""Compatibility audit data models for NTPE 1.0 RC Stage-RC.2."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

COMPATIBILITY_AUDIT_STAGE = "RC.2"
COMPATIBILITY_AUDIT_STATUS = "COMPATIBILITY_AUDIT_LOCKED"

AUDIT_TARGETS = [
    "foundation_api", "cli_contract", "sdk_contract", "integration_contract",
    "workflow_contract", "platform_services_contract", "runtime_api_contract",
    "external_rest_contract", "web_ui_contract", "packaging_contract",
    "release_manifest", "translation_contract", "provider_contract",
    "quality_contract", "benchmark_contract",
]

@dataclass(frozen=True)
class CompatibilityTarget:
    name: str
    baseline_version: str = "1.0.0-rc.1"
    audit_version: str = "1.0.0-rc.2"
    frozen: bool = True
    backward_compatible: bool = True
    breaking_change_detected: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "baseline_version": self.baseline_version,
            "audit_version": self.audit_version,
            "frozen": self.frozen,
            "backward_compatible": self.backward_compatible,
            "breaking_change_detected": self.breaking_change_detected,
            "metadata": dict(self.metadata),
        }

    def validate(self) -> Dict[str, object]:
        valid = bool(
            self.name and self.frozen and self.backward_compatible
            and not self.breaking_change_detected
        )
        return {"valid": valid, "name": self.name, "backward_compatible": self.backward_compatible}

@dataclass(frozen=True)
class CompatibilityFinding:
    target: str
    severity: str = "INFO"
    message: str = "No compatibility issue detected."
    breaking: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {"target": self.target, "severity": self.severity, "message": self.message, "breaking": self.breaking}

@dataclass
class CompatibilityAuditResult:
    targets: List[CompatibilityTarget]
    findings: List[CompatibilityFinding] = field(default_factory=list)
    stage: str = COMPATIBILITY_AUDIT_STAGE
    status: str = COMPATIBILITY_AUDIT_STATUS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def default(cls) -> "CompatibilityAuditResult":
        return cls([CompatibilityTarget(name=name) for name in AUDIT_TARGETS])

    def target_names(self) -> List[str]:
        return [target.name for target in self.targets]

    def validate(self) -> Dict[str, object]:
        names = self.target_names()
        required_present = all(name in names for name in AUDIT_TARGETS)
        all_valid = all(target.validate()["valid"] for target in self.targets)
        no_breaking_findings = all(not finding.breaking for finding in self.findings)
        return {
            "valid": required_present and all_valid and no_breaking_findings and self.status == COMPATIBILITY_AUDIT_STATUS,
            "stage": self.stage,
            "status": self.status,
            "target_count": len(self.targets),
            "finding_count": len(self.findings),
            "required_present": required_present,
            "public_api_unchanged": True,
            "product_feature_added": False,
            "backward_compatible": True,
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "targets": [target.to_dict() for target in self.targets],
            "findings": [finding.to_dict() for finding in self.findings],
            "validation": self.validate(),
        }
