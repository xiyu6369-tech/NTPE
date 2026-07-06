# =====================================================
# NTPE PS-01 Integration Launcher
# =====================================================
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(ROOT / 'ntpe_ps01_literary_prompt_engine_test.py')],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
