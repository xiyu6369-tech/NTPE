"""NTPE 1.0 RC Stage-RC.6 Release Candidate Freeze.

This module provides a small immutable freeze model used by the RC freeze
validation tests. It intentionally does not execute release logic or mutate any
runtime component.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, Iterable, List, Mapping


FROZEN_COMPONENTS: tuple[str, ...] = (
    "foundation",
    "cli",
    "sdk",
    "integration",
    "workflow",
    "platform_services",
    "runtime_api",
    "external_api",
    "web_ui",
    "packaging",
    "release_candidate",
)

REQUIRED_REPORTS: tuple[str, ...] = (
    "Regression_Report_RC_05.md",
    "Compatibility_Report_RC_05.md",
    "Translation_Regression_Report_RC_05.md",
    "Performance_Report_RC_05.md",
    "Release_Candidate_Validation_Report_RC_05.md",
)


@dataclass(frozen=True)
class RCFreezeManifest:
    """Immutable RC freeze manifest."""

    stage: str = "RC.6"
    status: str = "FROZEN"
    version: str = "1.0-rc"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frozen_components: tuple[str, ...] = FROZEN_COMPONENTS
    required_reports: tuple[str, ...] = REQUIRED_REPORTS
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> bool:
        return (
            self.stage == "RC.6"
            and self.status == "FROZEN"
            and len(self.frozen_components) >= 10
            and set(REQUIRED_REPORTS).issubset(set(self.required_reports))
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "version": self.version,
            "generated_at": self.generated_at,
            "frozen_components": list(self.frozen_components),
            "required_reports": list(self.required_reports),
            "metadata": dict(self.metadata),
        }

    def freeze_hash(self) -> str:
        payload = "|".join([
            self.stage,
            self.status,
            self.version,
            ",".join(self.frozen_components),
            ",".join(self.required_reports),
        ])
        return sha256(payload.encode("utf-8")).hexdigest()


class RCFreezeValidator:
    """Validates RC freeze readiness from manifest-like objects."""

    def __init__(self, manifest: RCFreezeManifest | None = None) -> None:
        self.manifest = manifest or RCFreezeManifest()

    def validate_components(self, components: Iterable[str] | None = None) -> bool:
        component_set = set(components or self.manifest.frozen_components)
        return set(FROZEN_COMPONENTS).issubset(component_set)

    def validate_reports(self, reports: Iterable[str] | None = None) -> bool:
        report_set = set(reports or self.manifest.required_reports)
        return set(REQUIRED_REPORTS).issubset(report_set)

    def run(self) -> Dict[str, object]:
        component_ok = self.validate_components()
        report_ok = self.validate_reports()
        manifest_ok = self.manifest.validate()
        return {
            "stage": self.manifest.stage,
            "status": "PASS" if component_ok and report_ok and manifest_ok else "FAIL",
            "component_validation": component_ok,
            "report_validation": report_ok,
            "manifest_validation": manifest_ok,
            "freeze_hash": self.manifest.freeze_hash(),
        }


def create_rc_freeze_manifest(**metadata: str) -> RCFreezeManifest:
    return RCFreezeManifest(metadata=metadata)
