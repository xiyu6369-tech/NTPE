"""Release freeze models and helpers for NTPE Stage-14.6."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .release_validator import ReleaseValidator, build_release_validation, load_release_validation
from .release_manifest import build_release_manifest
from .build_profiles import build_profile_manifest
from .distribution_builder import build_distribution_package
from .package_errors import PackageBuildError

FROZEN_RELEASE_COMPONENTS = (
    "Foundation v1.0",
    "CLI",
    "Integration",
    "Workflow",
    "Platform Services",
    "Runtime API",
    "External API",
    "Web UI",
    "Packaging Core",
    "Release Manifest",
    "Build Profiles",
    "Distribution Package",
    "Release Validation",
)

RELEASE_FREEZE_REQUIRED_REPORTS = (
    "Translation_Validation_Report_Stage_14_6.md",
    "Release_Validation_Report_Stage_14_6.md",
)


@dataclass
class ReleaseFreezeRecord:
    """Immutable-style freeze record for a release stage."""

    stage: str = "Stage-14.6"
    version: str = "1.0.0-beta"
    status: str = "FROZEN"
    components: List[str] = field(default_factory=lambda: list(FROZEN_RELEASE_COMPONENTS))
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if self.stage != "Stage-14.6":
            errors.append("stage must be Stage-14.6")
        if self.status != "FROZEN":
            errors.append("status must be FROZEN")
        missing_components = [name for name in FROZEN_RELEASE_COMPONENTS if name not in self.components]
        if missing_components:
            errors.append(f"missing frozen components: {missing_components}")
        if not self.version:
            errors.append("missing version")
        return {
            "valid": not errors,
            "errors": errors,
            "component_count": len(self.components),
            "artifact_count": len(self.artifacts),
            "compatibility": {
                "additive_only": True,
                "frozen_api_safe": True,
                "release_freeze_only": True,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "status": self.status,
            "components": list(self.components),
            "artifacts": list(self.artifacts),
            "metadata": dict(self.metadata),
            "validation": self.validate(),
        }


class ReleaseFreezer:
    """Creates a release freeze record without changing frozen project APIs."""

    def __init__(self, project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta"):
        self.project_root = Path(project_root)
        self.release_root = Path(release_root or self.project_root / "release")
        self.profile = profile
        if not self.project_root.exists():
            raise PackageBuildError(f"project root does not exist: {self.project_root}")

    def collect_artifacts(self) -> List[str]:
        candidates = [
            "Packaging_Manifest_Stage_14_1.json",
            "Release_Manifest_Stage_14_2.json",
            "Build_Profiles_Stage_14_3.json",
            "Distribution_Package_Stage_14_4.json",
            "Release_Validation_Stage_14_5.json",
            "Release_Freeze_Manifest_Stage_14_6.json",
            *RELEASE_FREEZE_REQUIRED_REPORTS,
        ]
        found: List[str] = []
        for name in candidates:
            matches = sorted(self.project_root.rglob(name))
            if matches:
                found.append(str(matches[0].relative_to(self.project_root)))
        return found

    def freeze(self) -> ReleaseFreezeRecord:
        release_validation = build_release_validation(self.project_root, self.release_root, self.profile)
        loaded_validation = load_release_validation(release_validation["report_path"])
        release_manifest = build_release_manifest(self.project_root)
        profile_manifest = build_profile_manifest(self.project_root)
        distribution = build_distribution_package(self.project_root, self.release_root, self.profile)
        validator_summary = ReleaseValidator(self.project_root, self.release_root, self.profile).run().validate()

        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "profile": self.profile,
            "release_validation_valid": loaded_validation["validation"]["valid"],
            "release_manifest_valid": release_manifest["validation"]["valid"],
            "build_profiles_valid": profile_manifest["validation"]["valid"],
            "distribution_valid": distribution["validation"]["valid"],
            "validator_check_count": validator_summary["check_count"],
            "frozen_api_policy": "no public API changes after Stage-14.6 without a new version plan",
        }
        return ReleaseFreezeRecord(artifacts=self.collect_artifacts(), metadata=metadata)


def build_release_freeze(project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta") -> Dict[str, Any]:
    freezer = ReleaseFreezer(project_root, release_root, profile)
    record = freezer.freeze()
    manifest_dir = freezer.release_root / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "Release_Freeze_Manifest_Stage_14_6.json"
    manifest_path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    data = record.to_dict()
    data["manifest_path"] = str(manifest_path)
    return data


def load_release_freeze(path: str | Path) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    record = ReleaseFreezeRecord(
        stage=data.get("stage", ""),
        version=data.get("version", ""),
        status=data.get("status", ""),
        components=list(data.get("components", [])),
        artifacts=list(data.get("artifacts", [])),
        metadata=dict(data.get("metadata", {})),
    )
    loaded = record.to_dict()
    loaded["manifest_path"] = str(path)
    return loaded
