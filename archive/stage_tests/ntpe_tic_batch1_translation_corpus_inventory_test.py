from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sandbox = ROOT / ".ntpe_test_sandbox" / "tic_batch1_root" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/integration/tic_batch1_translation_corpus_inventory_test.py",
            "--basetemp",
            str(sandbox),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "10 passed" in result.stdout, result.stdout
    finally:
        shutil.rmtree(ROOT / ".ntpe_test_sandbox" / "tic_batch1_root", ignore_errors=True)
    statistics = json.loads(
        (ROOT / "artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json").read_text(encoding="utf-8")
    )
    assert statistics["historical_translations"] > 0
    print("TIC Batch 1 Historical Translation Corpus Inventory ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
