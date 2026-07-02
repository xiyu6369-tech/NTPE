"""Launcher for Stage-12.1 External API / REST Core."""
from rest_api_core_test import (
    test_health_route,
    test_rest_api_created,
    test_rest_models,
    test_runtime_execute_route,
    test_runtime_execute_validation,
    test_unknown_route,
)


def main():
    checks = [
        ("REST Models", test_rest_models),
        ("REST API Created", test_rest_api_created),
        ("Health Route", test_health_route),
        ("Runtime Execute", test_runtime_execute_route),
        ("Execute Validation", test_runtime_execute_validation),
        ("Unknown Route", test_unknown_route),
    ]
    print("NTPE Stage-12.1 External API / REST Core Test")
    print("=" * 52)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
