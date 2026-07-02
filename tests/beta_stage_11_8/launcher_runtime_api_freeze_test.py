"""Launcher for Stage-11.8 Runtime API Freeze test."""
from runtime_api_freeze_test import test_freeze_report_contract, test_runtime_api_core_freeze_validation


def main():
    checks = [
        ("Freeze Report", test_freeze_report_contract),
        ("Core Freeze Validation", test_runtime_api_core_freeze_validation),
    ]
    print("NTPE Stage-11.8 Runtime API Freeze Test")
    print("=" * 48)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
