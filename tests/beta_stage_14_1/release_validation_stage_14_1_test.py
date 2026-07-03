"""Release validation guard for Stage-14.1."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from packaging import DEFAULT_RELEASE_DIRECTORIES, PackageBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_validation_stage_14_1():
    result = PackageBuilder(PROJECT_ROOT).build().to_dict()
    assert result["passed"] is True
    assert set(DEFAULT_RELEASE_DIRECTORIES).issubset(set(result["layout"]["directories"]))
    assert result["artifacts"]["valid"] is True
    assert Path(result["manifest_path"]).exists()


if __name__ == "__main__":
    test_release_validation_stage_14_1()
    print("PASS")
