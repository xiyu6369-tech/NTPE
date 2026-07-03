"""Stage-14.1 Packaging Core tests."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from packaging import (
    DEFAULT_RELEASE_DIRECTORIES,
    PACKAGING_STAGE,
    ArtifactManager,
    PackageBuilder,
    PackageLayout,
    PackageMetadata,
    load_packaging_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_package_metadata_created():
    metadata = PackageMetadata()
    data = metadata.to_dict()
    assert data["name"] == "ntpe"
    assert data["stage"] == PACKAGING_STAGE
    assert "runtime_api" in data["components"]
    assert "external_api" in data["components"]
    assert "web_ui" in data["components"]


def test_package_layout_created():
    layout = PackageLayout(PROJECT_ROOT / "release")
    layout.create()
    result = layout.validate()
    assert result["valid"] is True
    for name in DEFAULT_RELEASE_DIRECTORIES:
        assert name in result["directories"]


def test_artifact_registry_validates():
    manager = ArtifactManager()
    release_root = PROJECT_ROOT / "release"
    manager.register("reports", "directory", release_root / "reports")
    manager.register("manifests", "directory", release_root / "manifests")
    result = manager.validate()
    assert result["valid"] is True
    assert result["count"] == 2


def test_package_builder_builds_manifest():
    builder = PackageBuilder(PROJECT_ROOT)
    result = builder.build().to_dict()
    assert result["passed"] is True
    assert result["metadata"]["stage"] == PACKAGING_STAGE
    manifest = load_packaging_manifest(result["manifest_path"])
    assert manifest["uses_frozen_runtime_api"] is True
    assert manifest["uses_frozen_external_api"] is True
    assert manifest["additive_only"] is True


if __name__ == "__main__":
    test_package_metadata_created()
    test_package_layout_created()
    test_artifact_registry_validates()
    test_package_builder_builds_manifest()
    print("PASS")
