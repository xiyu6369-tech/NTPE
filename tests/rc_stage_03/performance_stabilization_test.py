from pathlib import Path
from performance.stabilization import PerformanceBaseline, PerformanceStabilizer, build_performance_stabilization_manifest

ROOT = Path(__file__).resolve().parents[2]

def test_performance_baseline_valid():
    baseline = PerformanceBaseline.default()
    validation = baseline.validate()
    assert validation["valid"] is True
    assert validation["performance_regression_detected"] is False

def test_performance_stabilizer_passes():
    result = PerformanceStabilizer(ROOT).run()
    assert result["passed"] is True
    assert result["stabilization"]["rc2_compatibility_preserved"] is True

def test_performance_manifest_written():
    built = build_performance_stabilization_manifest(ROOT)
    assert Path(built["manifest_path"]).exists()
    assert Path(built["hash_path"]).exists()
    assert built["result"]["status"] == "PASS"
