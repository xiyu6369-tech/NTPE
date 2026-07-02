"""Launcher for Stage-13.8 Web UI Freeze test."""
from web_ui_freeze_test import (
    test_web_ui_freeze_report_created,
    test_web_ui_freeze_validation_passes,
    test_web_ui_freeze_routes_are_present,
    test_web_ui_freeze_preserves_page_boundaries,
)


def main():
    checks = [
        ("Web UI Freeze Report", test_web_ui_freeze_report_created),
        ("Web UI Freeze Validation", test_web_ui_freeze_validation_passes),
        ("Frozen Routes Present", test_web_ui_freeze_routes_are_present),
        ("Page Boundary Compatibility", test_web_ui_freeze_preserves_page_boundaries),
    ]
    print("NTPE Stage-13.8 Web UI Freeze Test")
    print("=" * 42)
    for name, fn in checks:
        fn()
        print(f"{name:<34} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
