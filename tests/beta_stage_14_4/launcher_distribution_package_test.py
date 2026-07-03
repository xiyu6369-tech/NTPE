"""NTPE 1.0 Beta Stage-14.4 Distribution Package test."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import (  # noqa: E402
    DistributionBuilder,
    DistributionPackage,
    build_distribution_package,
    load_distribution_package_manifest,
)


def check(label: str, condition: bool) -> None:
    print(f"{label:<38} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE 1.0 Beta — Stage-14.4 Distribution Package Test")
    print("=" * 62)

    package = DistributionPackage(kind="full", name="sample", path="release/full/sample.zip")
    check("Distribution Package", package.validate()["valid"])

    builder = DistributionBuilder(ROOT, profile="beta")
    planned = builder.plan()
    validation = builder.validate(planned)
    check("Builder Created", isinstance(builder, DistributionBuilder))
    check("Plan Created", len(planned) >= 5)
    check("Full Package Planned", "full" in validation["kinds"])
    check("Increment Planned", "increment" in validation["kinds"])
    check("Portable Planned", "portable" in validation["kinds"])
    check("Source Planned", "source" in validation["kinds"])
    check("Release Bundle Planned", "release_bundle" in validation["kinds"])
    check("Validation", validation["valid"])
    check("Frozen API Safe", validation["compatibility"]["frozen_api_safe"])

    result = build_distribution_package(ROOT)
    manifest = load_distribution_package_manifest(result["manifest_path"])
    check("Manifest Written", Path(result["manifest_path"]).exists())
    check("Manifest Loaded", manifest["validation"]["valid"])

    # Backward compatibility smoke checks for previous Stage-14 modules.
    from packaging import PackageBuilder, build_release_manifest, build_profile_manifest  # noqa: E402

    package_result = PackageBuilder(ROOT).build().to_dict()
    release_result = build_release_manifest(ROOT)
    profile_result = build_profile_manifest(ROOT)
    check("Stage-14.1 Compatibility", package_result["passed"])
    check("Stage-14.2 Compatibility", release_result["validation"]["valid"])
    check("Stage-14.3 Compatibility", profile_result["validation"]["valid"])

    print("PASS")


if __name__ == "__main__":
    main()
