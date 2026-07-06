import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
result = subprocess.run([sys.executable, str(ROOT / 'ntpe_stage18_13_translation_quality_stabilization_test.py')], cwd=ROOT, text=True, capture_output=True)
print(result.stdout, end='')
if result.returncode != 0:
    print(result.stderr, end='')
    raise SystemExit(result.returncode)
