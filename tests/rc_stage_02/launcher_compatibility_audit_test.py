from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
"""Launcher for NTPE 1.0 RC Stage-RC.2 Compatibility Audit."""
from compatibility_audit_test import test_audit_registry_created, test_audit_runner_passes, test_manifest_written
from api_contract_audit_test import test_runtime_and_rest_contracts_compatible, test_cli_sdk_contracts_compatible
from ui_packaging_audit_test import test_webui_packaging_release_contracts_compatible
from translation_compatibility_test import test_translation_provider_quality_contracts_compatible

def main():
    checks = [
        ("Audit Registry", test_audit_registry_created),
        ("Audit Runner", test_audit_runner_passes),
        ("Manifest Written", test_manifest_written),
        ("Runtime REST Contract", test_runtime_and_rest_contracts_compatible),
        ("CLI SDK Contract", test_cli_sdk_contracts_compatible),
        ("WebUI Packaging Release", test_webui_packaging_release_contracts_compatible),
        ("Translation Compatibility", test_translation_provider_quality_contracts_compatible),
    ]
    print("NTPE 1.0 RC — Stage-RC.2 Compatibility Audit Test")
    print("=" * 60)
    for name, fn in checks:
        fn()
        print(f"{name:<34} PASS")
    print("PASS")

if __name__ == "__main__":
    main()
