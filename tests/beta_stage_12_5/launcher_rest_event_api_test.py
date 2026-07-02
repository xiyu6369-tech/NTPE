"""Launcher for Stage-12.5 REST Event API."""
from rest_event_api_test import (
    test_event_not_found,
    test_filter_summary_and_clear_events,
    test_method_validation,
    test_publish_get_list_event,
    test_rest_event_api_created,
)


def main():
    checks = [
        ("REST Event API Created", test_rest_event_api_created),
        ("Publish Get List Event", test_publish_get_list_event),
        ("Filter Summary Clear", test_filter_summary_and_clear_events),
        ("Event Not Found", test_event_not_found),
        ("Method Validation", test_method_validation),
    ]
    print("NTPE Stage-12.5 REST Event API Test")
    print("=" * 46)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
