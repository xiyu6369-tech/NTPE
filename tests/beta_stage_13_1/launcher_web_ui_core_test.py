"""Launcher for Stage-13.1 Web UI Core test."""
from web_ui_core_test import (
    test_web_ui_app_manifest_boundary,
    test_web_ui_render_dashboard,
    test_web_ui_route_registration,
    test_web_ui_shell_created,
)


def main():
    checks = [
        ("Web UI Shell", test_web_ui_shell_created),
        ("Route Registration", test_web_ui_route_registration),
        ("External API Boundary", test_web_ui_app_manifest_boundary),
        ("Dashboard Render", test_web_ui_render_dashboard),
    ]
    print("NTPE Stage-13.1 Web UI Core Test")
    print("=" * 42)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
