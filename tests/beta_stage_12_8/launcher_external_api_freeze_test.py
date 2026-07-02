"""Launcher for Stage-12.8 External API Freeze test."""
from external_api_freeze_test import (
    test_external_api_freeze_validation,
    test_external_api_runtime_boundary,
    test_freeze_report_contract,
)


def main():
    checks = [
        ("Freeze Report", test_freeze_report_contract),
        ("REST Freeze Validation", test_external_api_freeze_validation),
        ("Runtime Boundary", test_external_api_runtime_boundary),
    ]
    print("NTPE Stage-12.8 External API Freeze Test")
    print("=" * 50)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
