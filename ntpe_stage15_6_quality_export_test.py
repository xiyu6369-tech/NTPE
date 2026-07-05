# =====================================================
# NTPE 1.2 Professional
# Stage-15.6 Quality Report / Export Layer Validation
# =====================================================

from tests.stage_15_6.launcher_quality_export_test import run


if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-15.6 Quality Export Test FAIL")
    print("Stage-15.6 Quality Export Test PASS")
