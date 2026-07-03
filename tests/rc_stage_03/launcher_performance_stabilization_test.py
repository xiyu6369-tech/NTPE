from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from performance_stabilization_test import test_performance_baseline_valid, test_performance_stabilizer_passes, test_performance_manifest_written
from regression_performance_test import test_performance_reports_written
from compatibility_performance_test import test_no_api_or_product_feature_change

def main():
    checks = [
        ("Performance Baseline", test_performance_baseline_valid),
        ("Performance Stabilizer", test_performance_stabilizer_passes),
        ("Performance Manifest", test_performance_manifest_written),
        ("Performance Reports", test_performance_reports_written),
        ("No API Feature Change", test_no_api_or_product_feature_change),
    ]
    print("NTPE 1.0 RC — Stage-RC.3 Performance Stabilization Test")
    print("=" * 68)
    for name, fn in checks:
        fn()
        print(f"{name:<34} PASS")
    print("PASS")

if __name__ == "__main__":
    main()
