"""Distribution package builder for NTPE Stage-14.4."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .build_profiles import BuildProfileRegistry
from .distribution_package import DistributionPackage, VALID_DISTRIBUTION_KINDS, ensure_distribution_package
from .package_errors import PackageBuildError

DEFAULT_DISTRIBUTION_LAYOUT = {
    "full": "release/full",
    "increment": "release/increment",
    "portable": "release/portable",
    "wheel": "release/wheel",
    "source": "release/source",
    "release_bundle": "release/bundles",
}


@dataclass
class DistributionBuildResult:
    stage: str = "Stage-14.4"
    packages: List[DistributionPackage] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    manifest_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "package_count": len(self.packages),
            "packages": [package.to_dict() for package in self.packages],
            "validation": dict(self.validation),
            "manifest_path": self.manifest_path,
        }


class DistributionBuilder:
    """Plans NTPE distribution artifacts without modifying frozen runtime layers."""

    def __init__(self, project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta"):
        self.project_root = Path(project_root)
        self.release_root = Path(release_root or self.project_root / "release")
        self.profile_name = profile
        if not self.project_root.exists():
            raise PackageBuildError(f"project root does not exist: {self.project_root}")

    def _package_for_kind(self, kind: str, profile: str) -> DistributionPackage:
        target_dir = self.project_root / DEFAULT_DISTRIBUTION_LAYOUT[kind]
        target_dir.mkdir(parents=True, exist_ok=True)
        suffix = {
            "full": "Full.zip",
            "increment": "Increment.zip",
            "portable": "Portable.zip",
            "wheel": "Wheel.whl",
            "source": "Source.tar.gz",
            "release_bundle": "Release_Bundle.zip",
        }[kind]
        name = f"NTPE_Stage_14_4_{suffix}"
        includes = {
            "full": ["all project files", "tests", "reports", "release manifests"],
            "increment": ["Stage-14.4 changed files only"],
            "portable": ["runtime", "CLI", "REST", "Web UI", "configs"],
            "wheel": ["python package metadata", "runtime modules"],
            "source": ["source tree", "documentation", "manifests"],
            "release_bundle": ["full", "increment", "portable", "wheel", "source", "reports"],
        }[kind]
        return ensure_distribution_package(
            DistributionPackage(
                kind=kind,
                name=name,
                path=str(target_dir / name),
                profile=profile,
                includes=includes,
                metadata={
                    "stage": "Stage-14.4",
                    "additive_only": True,
                    "frozen_api_safe": True,
                    "planned_artifact": True,
                },
            )
        )

    def plan(self, kinds: Iterable[str] | None = None) -> List[DistributionPackage]:
        registry = BuildProfileRegistry.default()
        profile = registry.require(self.profile_name)
        selected = list(kinds or profile.artifact_kinds)
        # Release bundle is always part of Stage-14.4 planning.
        if "release_bundle" not in selected:
            selected.append("release_bundle")
        invalid = [kind for kind in selected if kind not in VALID_DISTRIBUTION_KINDS]
        if invalid:
            raise PackageBuildError("invalid distribution kinds: " + ", ".join(invalid))
        return [self._package_for_kind(kind, profile.name) for kind in selected]

    def validate(self, packages: Iterable[DistributionPackage]) -> Dict[str, Any]:
        package_list = list(packages)
        invalid = [package.to_dict() for package in package_list if not package.validate()["valid"]]
        kinds = [package.kind for package in package_list]
        required = ["full", "increment", "portable", "source", "release_bundle"]
        missing = [kind for kind in required if kind not in kinds]
        return {
            "valid": not invalid and not missing,
            "package_count": len(package_list),
            "kinds": kinds,
            "missing": missing,
            "invalid": invalid,
            "compatibility": {
                "uses_stage_14_3_build_profiles": True,
                "additive_only": True,
                "frozen_api_safe": True,
            },
        }

    def build(self) -> DistributionBuildResult:
        packages = self.plan()
        validation = self.validate(packages)
        manifest_dir = self.release_root / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "Distribution_Package_Stage_14_4.json"
        result = DistributionBuildResult(packages=packages, validation=validation, manifest_path=str(manifest_path))
        manifest_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return result


def build_distribution_package(project_root: str | Path, release_root: str | Path | None = None, profile: str = "beta") -> Dict[str, Any]:
    return DistributionBuilder(project_root, release_root, profile).build().to_dict()


def load_distribution_package_manifest(path: str | Path) -> Dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise PackageBuildError(f"distribution package manifest does not exist: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))
