import subprocess,sys
from pathlib import Path
if __name__=='__main__':raise SystemExit(subprocess.run([sys.executable,'-m','pytest','tests/unit/test_lcr_bounded_dual_pass_pilot.py','tests/unit/test_lcr_pilot_authorization.py','tests/integration/lcr_batch105_bounded_dual_pass_pilot_integration_test.py','-q'],cwd=Path(__file__).parent).returncode)
