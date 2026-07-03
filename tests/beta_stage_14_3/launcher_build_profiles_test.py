"""NTPE 1.0 Beta Stage-14.3 Build Profiles test."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging import (  # noqa: E402
    DEFAULT_PROFILE_ORDER,
    BuildProfile,
    BuildProfileRegistry,
    build_profile_manifest,
    load_build_profiles,
)


def check(label: str, condition: bool) -> None:
    print(f"{label:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE 1.0 Beta — Stage-14.3 Build Profiles Test")
    print("=" * 56)

    registry = BuildProfileRegistry.default()
    validation = registry.validate()
    check("Registry Created", isinstance(registry, BuildProfileRegistry))
    check("Default Profiles", validation["valid"])
    check("Profile Count", validation["count"] == 4)
    check("Profile Order", registry.names() == list(DEFAULT_PROFILE_ORDER))

    dev = registry.require("development")
    beta = registry.require("beta")
    rc = registry.require("rc")
    prod = registry.require("production")
    check("Development Profile", dev.debug and dev.include_tests)
    check("Beta Profile", beta.include_reports and "increment" in beta.artifact_kinds)
    check("RC Profile", rc.optimize and "wheel" in rc.artifact_kinds)
    check("Production Profile", prod.optimize and not prod.include_tests)

    custom = BuildProfile(name="custom", version_suffix="custom", artifact_kinds=["full"])
    registry.register(custom)
    check("Custom Profile", registry.require("custom").name == "custom")

    manifest_result = build_profile_manifest(ROOT)
    manifest = load_build_profiles(manifest_result["path"])
    check("Manifest Written", Path(manifest_result["path"]).exists())
    check("Manifest Validation", manifest["validation"]["valid"])
    check("Compatibility", manifest["compatibility"]["frozen_api_safe"])

    # Backward compatibility smoke checks for Stage-14.1 and Stage-14.2 modules.
    from packaging import PackageBuilder, build_release_manifest  # noqa: E402

    package_result = PackageBuilder(ROOT).build().to_dict()
    release_result = build_release_manifest(ROOT)
    check("Stage-14.1 Compatibility", package_result["passed"])
    check("Stage-14.2 Compatibility", release_result["validation"]["valid"])

    print("PASS")


if __name__ == "__main__":
    main()
