from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parent
TARGETS = (
    ROOT / "tests/unit/test_translation_quality_integration_v72.py",
    ROOT / "tests/unit/test_translation_quality_integration_v72_core.py",
    ROOT / "tests/integration/translation_engine_v720_milestone_a_translation_quality_integration_test.py",
    ROOT / "tests/integration/translation_engine_v720_milestone_a_runtime_memory_test.py",
    ROOT / "tests/performance/test_translation_quality_integration_v72_performance.py",
)


def test_milestone_a_focused_acceptance() -> None:
    assert pytest.main([*(str(path) for path in TARGETS), "-q"]) == 0


def main() -> int:
    return pytest.main([*(str(path) for path in TARGETS), "-q"])


if __name__ == "__main__":
    sys.exit(main())
