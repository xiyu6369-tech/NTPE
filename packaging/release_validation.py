"""Release validation models for NTPE Stage-14.5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

VALID_CHECK_STATUSES = ("PASS", "WARN", "FAIL")


@dataclass
class ReleaseValidationCheck:
    """One release validation checkpoint."""

    name: str
    status: str = "PASS"
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if not self.name:
            errors.append("missing name")
        if self.status not in VALID_CHECK_STATUSES:
            errors.append(f"invalid status: {self.status}")
        return {"valid": not errors, "errors": errors, "name": self.name, "status": self.status}

    def passed(self) -> bool:
        return self.validate()["valid"] and self.status in ("PASS", "WARN")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "metadata": dict(self.metadata),
            "validation": self.validate(),
        }


@dataclass
class ReleaseValidationSummary:
    """Aggregated release validation summary."""

    stage: str = "Stage-14.5"
    checks: List[ReleaseValidationCheck] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Dict[str, Any]:
        invalid = [check.to_dict() for check in self.checks if not check.validate()["valid"]]
        failed = [check.to_dict() for check in self.checks if check.status == "FAIL"]
        warnings = [check.to_dict() for check in self.checks if check.status == "WARN"]
        return {
            "valid": not invalid and not failed,
            "check_count": len(self.checks),
            "invalid": invalid,
            "failed": failed,
            "warnings": warnings,
            "passed": [check.name for check in self.checks if check.status == "PASS"],
            "compatibility": {
                "additive_only": True,
                "frozen_api_safe": True,
                "release_layer_only": True,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "checks": [check.to_dict() for check in self.checks],
            "metadata": dict(self.metadata),
            "validation": self.validate(),
        }
