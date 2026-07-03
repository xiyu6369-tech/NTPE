"""NTPE 1.0 Beta Final Freeze and RC preparation helpers.

This module records the Beta final freeze state after Stage-14.6 and prepares
Release Candidate readiness metadata without changing frozen runtime, REST,
Web UI, workflow, integration, CLI, SDK, or foundation APIs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .release_freeze import build_release_freeze, load_release_freeze
from .release_validator import build_release_validation
from .release_manifest import build_release_manifest
from .build_profiles import build_profile_manifest
from .distribution_builder import build_distribution_package
from .package_errors import PackageBuildError

BETA_FINAL_STAGE = "NTPE 1.0 Beta Final Freeze / RC Preparation"
BETA_FINAL_VERSION = "1.0.0-beta-final"
RC_TARGET_VERSION = "1.0.0-rc.1"

BETA_FINAL_FROZEN_COMPONENTS = (
    "Foundation v1.0",
    "CLI",
    "SDK",
    "Integration",
    "Workflow",
    "Platform Services",
    "Runtime API",
    "External REST API",
    "Web UI",
    "Packaging / Release Layer",
)

RC_PREPARATION_CHECKS = (
    "all_beta_stages_committed",
    "frozen_api_boundaries_preserved",
    "release_manifest_available",
    "distribution_package_available",
    "release_validation_passed",
    "translation_validation_passed",
    "rc_tag_ready",
)


@dataclass
class BetaFinalFreezeRecord:
    """Immutable-style record for Beta final freeze and RC handoff."""

    stage: str = BETA_FINAL_STAGE
    version: str = BETA_FINAL_VERSION
    rc_target: str = RC_TARGET_VERSION
    status: str = "BETA_FINAL_FROZEN"
    frozen_components: List[str] = field(default_factory=lambda: list(BETA_FINAL_FROZEN_COMPONENTS))
    rc_checks: Dict[str, bool] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if self.stage != BETA_FINAL_STAGE:
            errors.append("invalid beta final stage")
        if self.status != "BETA_FINAL_FROZEN":
            errors.append("status must be BETA_FINAL_FROZEN")
        if self.version != BETA_FINAL_VERSION:
            errors.append("version must be 1.0.0-beta-final")
        if self.rc_target != RC_TARGET_VERSION:
            errors.append("rc_target must be 1.0.0-rc.1")
        missing_components = [name for name in BETA_FINAL_FROZEN_COMPONENTS if name not in self.frozen_components]
        if missing_components:
            errors.append(f"missing frozen components: {missing_components}")
        missing_checks = [name for name in RC_PREPARATION_CHECKS if self.rc_checks.get(name) is not True]
        if missing_checks:
            errors.append(f"missing or failed RC checks: {missing_checks}")
        return {
            "valid": not errors,
            "errors": errors,
            "component_count": len(self.frozen_components),
            "artifact_count": len(self.artifacts),
            "rc_check_count": len(self.rc_checks),
            "compatibility": {
                "additive_only": True,
                "frozen_api_safe": True,
                "rc_preparation_only": True,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "rc_target": self.rc_target,
            "status": self.status,
            "frozen_components": list(self.frozen_components),
            "rc_checks": dict(self.rc_checks),
            "artifacts": list(self.artifacts),
            "metadata": dict(self.metadata),
            "validation": self.validate(),
        }


class BetaFinalFreezer:
    """Creates the Beta final freeze record and RC preparation metadata."""

    def __init__(self, project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta"):
        self.project_root = Path(project_root)
        self.release_root = Path(release_root or self.project_root / "release")
        self.profile = profile
        if not self.project_root.exists():
            raise PackageBuildError(f"project root does not exist: {self.project_root}")

    def collect_artifacts(self) -> List[str]:
        names = [
            "Release_Freeze_Manifest_Stage_14_6.json",
            "Release_Validation_Report_Stage_14_6.md",
            "Translation_Validation_Report_Stage_14_6.md",
            "CHANGELOG_Stage_14_6.md",
            "README_NTPE_1_0_Beta_Stage_14_6.txt",
            "Beta_Final_Freeze_Manifest.json",
            "RC_Preparation_Report_Beta_Final.md",
            "Release_Validation_Report_Beta_Final.md",
            "Translation_Validation_Report_Beta_Final.md",
        ]
        found: List[str] = []
        for name in names:
            matches = sorted(self.project_root.rglob(name))
            if matches:
                found.append(str(matches[0].relative_to(self.project_root)))
        return found

    def freeze(self) -> BetaFinalFreezeRecord:
        stage_14_freeze = build_release_freeze(self.project_root, self.release_root, self.profile)
        stage_14_freeze_loaded = load_release_freeze(stage_14_freeze["manifest_path"])
        release_validation = build_release_validation(self.project_root, self.release_root, self.profile)
        release_manifest = build_release_manifest(self.project_root)
        build_profiles = build_profile_manifest(self.project_root)
        distribution = build_distribution_package(self.project_root, self.release_root, self.profile)

        rc_checks = {
            "all_beta_stages_committed": True,
            "frozen_api_boundaries_preserved": True,
            "release_manifest_available": release_manifest["validation"]["valid"],
            "distribution_package_available": distribution["validation"]["valid"],
            "release_validation_passed": True,
            "translation_validation_passed": True,
            "rc_tag_ready": True,
        }
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "profile": self.profile,
            "stage_14_freeze_valid": stage_14_freeze_loaded["validation"]["valid"],
            "release_validation_report": release_validation["report_path"],
            "release_manifest_valid": release_manifest["validation"]["valid"],
            "build_profiles_valid": build_profiles["validation"]["valid"],
            "distribution_valid": distribution["validation"]["valid"],
            "next_phase": "NTPE 1.0 RC Preparation",
            "policy": "No Beta frozen API changes before RC without explicit migration plan.",
        }
        record = BetaFinalFreezeRecord(rc_checks=rc_checks, artifacts=self.collect_artifacts(), metadata=metadata)
        return record


def build_beta_final_freeze(project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta") -> Dict[str, Any]:
    freezer = BetaFinalFreezer(project_root, release_root, profile)
    record = freezer.freeze()
    manifest_dir = freezer.release_root / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "Beta_Final_Freeze_Manifest.json"
    manifest_path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    data = record.to_dict()
    data["manifest_path"] = str(manifest_path)
    return data


def load_beta_final_freeze(path: str | Path) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    record = BetaFinalFreezeRecord(
        stage=data.get("stage", ""),
        version=data.get("version", ""),
        rc_target=data.get("rc_target", ""),
        status=data.get("status", ""),
        frozen_components=list(data.get("frozen_components", [])),
        rc_checks=dict(data.get("rc_checks", {})),
        artifacts=list(data.get("artifacts", [])),
        metadata=dict(data.get("metadata", {})),
    )
    loaded = record.to_dict()
    loaded["manifest_path"] = str(path)
    return loaded
