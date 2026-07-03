"""NTPE 1.0 Beta Stage-14.5 Release Validation test."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import (  # noqa: E402
    ReleaseValidationCheck,
    ReleaseValidator,
    build_release_validation,
    load_release_validation,
    PackageBuilder,
    build_release_manifest,
    build_profile_manifest,
    build_distribution_package,
)


def check(label: str, condition: bool) -> None:
    print(f"{label:<42} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE 1.0 Beta — Stage-14.5 Release Validation Test")
    print("=" * 68)

    check_item = ReleaseValidationCheck("Smoke Check", "PASS")
    check("Release Check Model", check_item.validate()["valid"])
    check("Release Check Pass State", check_item.passed())

    validator = ReleaseValidator(ROOT)
    summary = validator.run()
    validation = summary.validate()
    check("Validator Created", isinstance(validator, ReleaseValidator))
    check("Validation Summary", validation["valid"])
    check("Check Count", validation["check_count"] >= 8)
    check("Frozen API Safe", validation["compatibility"]["frozen_api_safe"])
    check("Release Layer Only", validation["compatibility"]["release_layer_only"])

    result = build_release_validation(ROOT)
    loaded = load_release_validation(result["report_path"])
    check("Report Written", Path(result["report_path"]).exists())
    check("Report Loaded", loaded["validation"]["valid"])

    # Backward compatibility smoke checks for Stage-14.1 through Stage-14.4.
    package_result = PackageBuilder(ROOT).build().to_dict()
    release_result = build_release_manifest(ROOT)
    profile_result = build_profile_manifest(ROOT)
    distribution_result = build_distribution_package(ROOT)
    check("Stage-14.1 Compatibility", package_result["passed"])
    check("Stage-14.2 Compatibility", release_result["validation"]["valid"])
    check("Stage-14.3 Compatibility", profile_result["validation"]["valid"])
    check("Stage-14.4 Compatibility", distribution_result["validation"]["valid"])

    print("PASS")


if __name__ == "__main__":
    main()
