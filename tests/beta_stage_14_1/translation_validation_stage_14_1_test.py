"""Translation validation guard for Stage-14.1."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from packaging import PackageBuilder, load_packaging_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_translation_validation_stage_14_1():
    builder = PackageBuilder(PROJECT_ROOT)
    result = builder.build().to_dict()
    manifest = load_packaging_manifest(result["manifest_path"])
    assert result["passed"] is True
    assert manifest["uses_frozen_runtime_api"] is True
    assert manifest["uses_frozen_external_api"] is True
    assert manifest["additive_only"] is True
    for component in ["workflow", "runtime_api", "external_api", "web_ui", "packaging"]:
        assert component in manifest["metadata"]["components"]


if __name__ == "__main__":
    test_translation_validation_stage_14_1()
    print("PASS")
