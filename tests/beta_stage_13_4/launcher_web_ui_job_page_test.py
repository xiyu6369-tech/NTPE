"""Launcher for Stage-13.4 Web UI Job Page test."""
from web_ui_job_page_test import (
    test_job_page_created,
    test_job_page_manifest,
    test_job_page_render_component,
    test_job_page_summary,
)


def main():
    checks = [
        ("Job Page Created", test_job_page_created),
        ("Job Page Render Component", test_job_page_render_component),
        ("Job Page Summary", test_job_page_summary),
        ("Job Page Manifest", test_job_page_manifest),
    ]
    print("NTPE Stage-13.4 Web UI Job Page Test")
    print("=" * 44)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
