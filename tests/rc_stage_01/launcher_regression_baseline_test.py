"""Launcher for NTPE 1.0 RC Stage-RC.1 Regression Baseline."""
from regression_baseline_test import test_baseline_created, test_registry_created, test_runner_passes, test_manifest_written
from regression_runtime_test import test_runtime_api_frozen_component_present
from regression_rest_test import test_rest_api_frozen_component_present
from regression_webui_test import test_webui_frozen_component_present
from regression_packaging_test import test_packaging_release_components_present
from regression_translation_test import test_translation_regression_baseline

def main():
    checks = [
        ("Baseline Created", test_baseline_created),
        ("Registry Created", test_registry_created),
        ("Runner Passes", test_runner_passes),
        ("Manifest Written", test_manifest_written),
        ("Runtime Regression", test_runtime_api_frozen_component_present),
        ("REST Regression", test_rest_api_frozen_component_present),
        ("Web UI Regression", test_webui_frozen_component_present),
        ("Packaging Regression", test_packaging_release_components_present),
        ("Translation Regression", test_translation_regression_baseline),
    ]
    print("NTPE 1.0 RC — Stage-RC.1 Regression Baseline Test")
    print("=" * 60)
    for name, fn in checks:
        fn()
        print(f"{name:<34} PASS")
    print("PASS")

if __name__ == "__main__":
    main()
