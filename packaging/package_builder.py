"""Package builder facade for NTPE Stage-14.1."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from .artifact_manager import ArtifactManager
from .package_errors import PackageBuildError
from .package_layout import PackageLayout
from .package_metadata import PackageMetadata


@dataclass
class PackageBuildResult:
    metadata: Dict[str, Any]
    layout: Dict[str, Any]
    artifacts: Dict[str, Any]
    manifest_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "layout": self.layout,
            "artifacts": self.artifacts,
            "manifest_path": self.manifest_path,
            "passed": self.layout.get("valid", False) and self.artifacts.get("valid", False),
        }


@dataclass
class PackageBuilder:
    """Builds the stable packaging context used by later release stages."""

    project_root: Path
    release_root: Path | None = None
    metadata: PackageMetadata = field(default_factory=PackageMetadata)
    artifacts: ArtifactManager = field(default_factory=ArtifactManager)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root)
        self.release_root = Path(self.release_root or self.project_root / "release")

    def prepare_layout(self) -> PackageLayout:
        layout = PackageLayout(self.release_root)
        layout.create()
        return layout

    def register_default_artifacts(self) -> None:
        self.artifacts.register("full_zip", "zip", self.release_root / "full", required=True)
        self.artifacts.register("increment_zip", "zip", self.release_root / "increment", required=True)
        self.artifacts.register("portable", "directory", self.release_root / "portable", required=True)
        self.artifacts.register("wheel", "directory", self.release_root / "wheel", required=True)
        self.artifacts.register("source", "directory", self.release_root / "source", required=True)
        self.artifacts.register("reports", "directory", self.release_root / "reports", required=True)
        self.artifacts.register("manifests", "directory", self.release_root / "manifests", required=True)

    def build_manifest(self) -> Path:
        manifest_dir = self.release_root / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "Packaging_Manifest_Stage_14_1.json"
        payload = {
            "metadata": self.metadata.to_dict(),
            "artifacts": self.artifacts.list(),
            "release_root": str(self.release_root),
            "uses_frozen_runtime_api": True,
            "uses_frozen_external_api": True,
            "additive_only": True,
        }
        manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest_path

    def build(self) -> PackageBuildResult:
        if not self.project_root.exists():
            raise PackageBuildError(f"project root does not exist: {self.project_root}")
        layout = self.prepare_layout()
        self.register_default_artifacts()
        manifest_path = self.build_manifest()
        layout_validation = layout.validate()
        artifact_validation = self.artifacts.validate()
        return PackageBuildResult(
            metadata=self.metadata.to_dict(),
            layout=layout_validation,
            artifacts=artifact_validation,
            manifest_path=str(manifest_path),
        )


def load_packaging_manifest(path: str | Path) -> Dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise PackageBuildError(f"manifest does not exist: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))
