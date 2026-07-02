"""Launcher for Stage-12.3 REST Job API."""
from rest_job_api_test import (
    test_create_get_list_job,
    test_job_not_found,
    test_job_transitions_status_and_result,
    test_method_validation,
    test_rest_job_api_created,
)


def main():
    checks = [
        ("REST Job API Created", test_rest_job_api_created),
        ("Create Get List Job", test_create_get_list_job),
        ("Job Transitions", test_job_transitions_status_and_result),
        ("Job Not Found", test_job_not_found),
        ("Method Validation", test_method_validation),
    ]
    print("NTPE Stage-12.3 REST Job API Test")
    print("=" * 44)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
