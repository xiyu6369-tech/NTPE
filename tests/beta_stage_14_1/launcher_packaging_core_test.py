"""Launcher for Stage-14.1 Packaging Core test."""
from package_builder_test import (
    test_artifact_registry_validates,
    test_package_builder_builds_manifest,
    test_package_layout_created,
    test_package_metadata_created,
)


def main():
    checks = [
        ("Package Metadata", test_package_metadata_created),
        ("Package Layout", test_package_layout_created),
        ("Artifact Registry", test_artifact_registry_validates),
        ("Package Builder Manifest", test_package_builder_builds_manifest),
    ]
    print("NTPE Stage-14.1 Packaging Core Test")
    print("=" * 40)
    for name, fn in checks:
        fn()
        print(f"{name:<30} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
