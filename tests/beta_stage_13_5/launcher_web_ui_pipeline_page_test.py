"""Launcher for Stage-13.5 Web UI Pipeline Page test."""
from web_ui_pipeline_page_test import (
    test_pipeline_page_created,
    test_pipeline_page_manifest,
    test_pipeline_page_render_component,
    test_pipeline_page_summary,
)


def main():
    checks = [
        ("Pipeline Page Created", test_pipeline_page_created),
        ("Pipeline Page Render Component", test_pipeline_page_render_component),
        ("Pipeline Page Summary", test_pipeline_page_summary),
        ("Pipeline Page Manifest", test_pipeline_page_manifest),
    ]
    print("NTPE Stage-13.5 Web UI Pipeline Page Test")
    print("=" * 49)
    for name, fn in checks:
        fn()
        print(f"{name:<36} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
