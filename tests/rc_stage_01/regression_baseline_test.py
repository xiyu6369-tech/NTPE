"""RC.1 regression baseline tests."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from regression import RegressionBaseline, RegressionRegistry, RegressionRunner, build_regression_manifest, load_regression_manifest

def test_baseline_created():
    baseline = RegressionBaseline.default()
    validation = baseline.validate()
    assert validation["valid"] is True
    assert validation["component_count"] >= 15
    assert validation["frozen_api_safe"] is True
    assert validation["product_feature_added"] is False

def test_registry_created():
    registry = RegressionRegistry.default()
    assert "foundation" in registry.names()
    assert "runtime_api" in registry.names()
    assert "web_ui" in registry.names()
    assert registry.validate()["valid"] is True

def test_runner_passes():
    result = RegressionRunner(ROOT).run()
    assert result["passed"] is True
    assert result["status"] == "PASS"
    assert result["compatibility"]["frozen_api_safe"] is True
    assert result["compatibility"]["product_feature_added"] is False

def test_manifest_written():
    result = build_regression_manifest(ROOT)
    loaded = load_regression_manifest(result["manifest_path"])
    assert Path(result["manifest_path"]).exists()
    assert loaded["passed"] is True
    assert loaded["baseline"]["validation"]["valid"] is True

if __name__ == "__main__":
    test_baseline_created(); test_registry_created(); test_runner_passes(); test_manifest_written(); print("PASS")
