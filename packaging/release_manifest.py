"""Release manifest builder for NTPE Stage-14.2."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .artifact_manager import ArtifactManager
from .component_manifest import ComponentManifest
from .dependency_manifest import DependencyManifest
from .manifest_schema import ManifestSchema
from .package_errors import PackageBuildError


@dataclass
class ReleaseManifest:
    name: str = "ntpe"
    version: str = "1.0.0-beta"
    stage: str = "Stage-14.2"
    profile: str = "beta"
    components: ComponentManifest = field(default_factory=ComponentManifest.default_beta_components)
    dependencies: DependencyManifest = field(default_factory=DependencyManifest.default_beta_dependencies)
    artifacts: ArtifactManager = field(default_factory=ArtifactManager)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def register_default_artifacts(self, release_root: str | Path) -> None:
        root = Path(release_root)
        self.artifacts.register("full_zip", "zip", root / "full", required=True)
        self.artifacts.register("increment_zip", "zip", root / "increment", required=True)
        self.artifacts.register("release_manifest", "json", root / "manifests" / "Release_Manifest_Stage_14_2.json", required=False)
        self.artifacts.register("reports", "directory", root / "reports", required=True)
        self.artifacts.register("manifests", "directory", root / "manifests", required=True)

    def compatibility(self) -> Dict[str, bool]:
        return {
            "foundation_v1_frozen": True,
            "cli_frozen": True,
            "integration_frozen": True,
            "workflow_frozen": True,
            "platform_services_frozen": True,
            "runtime_api_frozen": True,
            "external_api_frozen": True,
            "web_ui_frozen": True,
            "additive_only": True,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "stage": self.stage,
            "profile": self.profile,
            "created_at": self.created_at,
            "components": self.components.to_list(),
            "dependencies": self.dependencies.to_list(),
            "artifacts": self.artifacts.list(),
            "compatibility": self.compatibility(),
        }

    def validate(self) -> Dict[str, Any]:
        payload = self.to_dict()
        schema_result = ManifestSchema().validate(payload)
        component_result = self.components.validate()
        dependency_result = self.dependencies.validate()
        artifact_result = self.artifacts.validate()
        return {
            "valid": all([
                schema_result["valid"],
                component_result["valid"],
                dependency_result["valid"],
                artifact_result["valid"],
            ]),
            "schema": schema_result,
            "components": component_result,
            "dependencies": dependency_result,
            "artifacts": artifact_result,
        }

    def write(self, path: str | Path) -> Path:
        manifest_path = Path(path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest_path


def build_release_manifest(project_root: str | Path, release_root: str | Path | None = None) -> Dict[str, Any]:
    root = Path(project_root)
    if not root.exists():
        raise PackageBuildError(f"project root does not exist: {root}")
    release = Path(release_root or root / "release")
    for name in ("full", "increment", "reports", "manifests"):
        (release / name).mkdir(parents=True, exist_ok=True)
    manifest = ReleaseManifest()
    manifest.register_default_artifacts(release)
    validation = manifest.validate()
    path = manifest.write(release / "manifests" / "Release_Manifest_Stage_14_2.json")
    return {"path": str(path), "validation": validation, "manifest": manifest.to_dict()}


def load_release_manifest(path: str | Path) -> Dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise PackageBuildError(f"release manifest does not exist: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))
