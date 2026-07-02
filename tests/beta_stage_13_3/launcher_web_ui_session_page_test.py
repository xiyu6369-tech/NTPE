"""Launcher for Stage-13.3 Web UI Session Page test."""
from web_ui_session_page_test import (
    test_session_page_created,
    test_session_page_manifest,
    test_session_page_render_component,
    test_session_page_summary,
)


def main():
    checks = [
        ("Session Page Created", test_session_page_created),
        ("Session Page Render Component", test_session_page_render_component),
        ("Session Page Summary", test_session_page_summary),
        ("Session Page Manifest", test_session_page_manifest),
    ]
    print("NTPE Stage-13.3 Web UI Session Page Test")
    print("=" * 48)
    for name, fn in checks:
        fn()
        print(f"{name:<36} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
