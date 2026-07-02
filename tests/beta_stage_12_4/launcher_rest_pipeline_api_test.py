"""Launcher for Stage-12.4 REST Pipeline API."""
from rest_pipeline_api_test import (
    test_add_stage_transitions_status_and_summary,
    test_create_get_list_pipeline,
    test_method_validation,
    test_pipeline_not_found,
    test_rest_pipeline_api_created,
)


def main():
    checks = [
        ("REST Pipeline API Created", test_rest_pipeline_api_created),
        ("Create Get List Pipeline", test_create_get_list_pipeline),
        ("Pipeline Transitions", test_add_stage_transitions_status_and_summary),
        ("Pipeline Not Found", test_pipeline_not_found),
        ("Method Validation", test_method_validation),
    ]
    print("NTPE Stage-12.4 REST Pipeline API Test")
    print("=" * 49)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
