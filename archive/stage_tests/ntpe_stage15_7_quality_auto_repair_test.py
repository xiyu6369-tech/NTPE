# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer Root Launcher
# =====================================================

from tests.stage_15_7.launcher_quality_auto_repair_test import run

if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-15.7 Launcher FAIL")
    print("Stage-15.7 Launcher PASS")
