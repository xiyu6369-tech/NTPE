"""Launcher for Stage-13.6 Web UI Event Page test."""
from web_ui_event_page_test import (
    test_event_page_created,
    test_event_page_manifest,
    test_event_publish_and_refresh,
    test_event_page_render_component,
    test_event_page_summary,
)


def main():
    checks = [
        ("Event Page Created", test_event_page_created),
        ("Event Page Render Component", test_event_page_render_component),
        ("Event Page Summary", test_event_page_summary),
        ("Event Page Manifest", test_event_page_manifest),
        ("Event Publish and Refresh", test_event_publish_and_refresh),
    ]
    print("NTPE Stage-13.6 Web UI Event Page Test")
    print("=" * 46)
    for name, fn in checks:
        fn()
        print(f"{name:<36} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
