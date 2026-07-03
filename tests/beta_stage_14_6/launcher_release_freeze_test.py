"""NTPE 1.0 Beta Stage-14.6 Release Freeze test."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import (  # noqa: E402
    FROZEN_RELEASE_COMPONENTS,
    ReleaseFreezeRecord,
    ReleaseFreezer,
    ReleaseValidator,
    build_release_freeze,
    load_release_freeze,
)


def check(label: str, condition: bool) -> None:
    print(f"{label:<42} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE 1.0 Beta — Stage-14.6 Release Freeze Test")
    print("=" * 68)

    record = ReleaseFreezeRecord(artifacts=["release/manifests/example.json"])
    validation = record.validate()
    check("Freeze Record Model", validation["valid"])
    check("Frozen Component Count", validation["component_count"] >= 12)
    check("Frozen API Safe", validation["compatibility"]["frozen_api_safe"])

    freezer = ReleaseFreezer(ROOT)
    freeze_record = freezer.freeze()
    freeze_validation = freeze_record.validate()
    check("Freezer Created", isinstance(freezer, ReleaseFreezer))
    check("Freeze Record Built", freeze_validation["valid"])
    check("Frozen Components", all(name in freeze_record.components for name in FROZEN_RELEASE_COMPONENTS))
    check("Release Validation Rechecked", freeze_record.metadata["release_validation_valid"])
    check("Distribution Rechecked", freeze_record.metadata["distribution_valid"])

    manifest = build_release_freeze(ROOT)
    loaded = load_release_freeze(manifest["manifest_path"])
    check("Freeze Manifest Written", Path(manifest["manifest_path"]).exists())
    check("Freeze Manifest Loaded", loaded["validation"]["valid"])
    check("Freeze Status", loaded["status"] == "FROZEN")

    # Stage-14.5 compatibility remains intact.
    validator_summary = ReleaseValidator(ROOT).run().validate()
    check("Stage-14.5 Compatibility", validator_summary["valid"])
    check("Release Layer Only", validator_summary["compatibility"]["release_layer_only"])

    print("PASS")


if __name__ == "__main__":
    main()
