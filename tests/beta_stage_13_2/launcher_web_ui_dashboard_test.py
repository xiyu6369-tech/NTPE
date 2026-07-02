"""Launcher for Stage-13.2 Web UI Dashboard test."""
from web_ui_dashboard_test import (
    test_dashboard_created,
    test_dashboard_manifest,
    test_dashboard_render_component,
    test_dashboard_summary,
)


def main():
    checks = [
        ("Dashboard Created", test_dashboard_created),
        ("Dashboard Render Component", test_dashboard_render_component),
        ("Dashboard Summary", test_dashboard_summary),
        ("Dashboard Manifest", test_dashboard_manifest),
    ]
    print("NTPE Stage-13.2 Web UI Dashboard Test")
    print("=" * 45)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
