from __future__ import annotations
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 for path in ("tests/unit/test_lcr_dual_pass_semantic_shadow.py","tests/integration/lcr_batch104_dual_pass_semantic_shadow_integration_test.py"):
  if subprocess.run([sys.executable,"-m","pytest",path,"-q"],cwd=ROOT).returncode:return 1
 print("LCR Batch 10.4 Dual-pass Semantic Shadow: ALL PASS");return 0
if __name__=="__main__":raise SystemExit(main())
