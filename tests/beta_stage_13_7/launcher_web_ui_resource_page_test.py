"""Launcher for Stage-13.7 Web UI Resource Page test."""
from web_ui_resource_page_test import (
    test_resource_page_created,
    test_resource_page_manifest,
    test_resource_create_and_refresh,
    test_resource_page_render_component,
    test_resource_page_summary,
)


def main():
    checks = [
        ("Resource Page Created", test_resource_page_created),
        ("Resource Page Render Component", test_resource_page_render_component),
        ("Resource Page Summary", test_resource_page_summary),
        ("Resource Page Manifest", test_resource_page_manifest),
        ("Resource Create and Refresh", test_resource_create_and_refresh),
    ]
    print("NTPE Stage-13.7 Web UI Resource Page Test")
    print("=" * 49)
    for name, fn in checks:
        fn()
        print(f"{name:<38} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
