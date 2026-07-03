"""Launcher for Stage-14.1 Release Validation."""
from release_validation_stage_14_1_test import test_release_validation_stage_14_1


def main():
    print("NTPE Release Validation Stage-14.1")
    print("=" * 39)
    test_release_validation_stage_14_1()
    print(f"{'Release Layout':<32} PASS")
    print(f"{'Artifact Registry':<32} PASS")
    print(f"{'Packaging Manifest':<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()
