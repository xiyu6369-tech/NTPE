from __future__ import annotations

import runpy
from pathlib import Path


def main() -> int:
    test_path = (
        Path(__file__).resolve().parent
        / "tests"
        / "integration"
        / "translation_quality_unified_gate_v531_test.py"
    )
    namespace = runpy.run_path(str(test_path))
    return int(namespace["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
