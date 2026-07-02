"""Launcher for Stage-12.6 REST Resource API."""
from rest_resource_api_test import (
    test_create_get_list_resource,
    test_filter_and_summary_resources,
    test_resource_lifecycle_actions,
    test_resource_not_found_and_method_validation,
    test_rest_resource_api_created,
)


def main():
    checks = [
        ("REST Resource API Created", test_rest_resource_api_created),
        ("Create Get List Resource", test_create_get_list_resource),
        ("Filter Summary Resource", test_filter_and_summary_resources),
        ("Resource Lifecycle", test_resource_lifecycle_actions),
        ("Error Method Validation", test_resource_not_found_and_method_validation),
    ]
    print("NTPE Stage-12.6 REST Resource API Test")
    print("=" * 49)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
