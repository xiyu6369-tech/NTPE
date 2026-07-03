"""NTPE 1.0 Beta Stage-14.2 Release Manifest tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import (  # noqa: E402
    ComponentManifest,
    DependencyManifest,
    ManifestSchema,
    ReleaseManifest,
    build_release_manifest,
    load_release_manifest,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta - Stage-14.2 Release Manifest Test")
    print("=" * 58)

    schema = ManifestSchema()
    manifest = ReleaseManifest()
    release_root = ROOT / "release"
    manifest.register_default_artifacts(release_root)

    check("Component Manifest", ComponentManifest.default_beta_components().validate()["valid"])
    check("Dependency Manifest", DependencyManifest.default_beta_dependencies().validate()["valid"])
    check("Schema Validation", schema.validate(manifest.to_dict())["valid"])
    check("Manifest Validation", manifest.validate()["valid"])

    result = build_release_manifest(ROOT, release_root)
    path = Path(result["path"])
    loaded = load_release_manifest(path)

    check("Manifest Written", path.exists())
    check("Manifest Loaded", loaded["stage"] == "Stage-14.2")
    check("Component Count", len(loaded["components"]) >= 10)
    check("Dependency Count", len(loaded["dependencies"]) >= 5)
    check("Compatibility Frozen", loaded["compatibility"]["runtime_api_frozen"])
    check("External API Frozen", loaded["compatibility"]["external_api_frozen"])
    check("Web UI Frozen", loaded["compatibility"]["web_ui_frozen"])
    check("Additive Only", loaded["compatibility"]["additive_only"])

    print("PASS")


if __name__ == "__main__":
    main()
