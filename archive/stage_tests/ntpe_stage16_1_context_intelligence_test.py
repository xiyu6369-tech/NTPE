# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine Root Launcher
# =====================================================

from tests.stage_16_1.launcher_context_intelligence_test import run

if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-16.1 Launcher FAIL")
    print("Stage-16.1 Launcher PASS")
