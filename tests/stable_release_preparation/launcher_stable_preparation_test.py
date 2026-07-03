from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stable_release.preparation import StablePreparationValidator, build_stable_preparation_artifacts


def main() -> int:
    root = Path.cwd()
    result = StablePreparationValidator(root).run()
    artifacts = build_stable_preparation_artifacts(root)
    checks = [
        ("Stable Preparation", result["status"] == "PASS"),
        ("RC Artifacts", result["validation"]["required_rc_artifacts_valid"] is True),
        ("Frozen Components", result["validation"]["component_validation"] is True),
        ("No Public API Change", result["validation"]["public_api_changed"] is False),
        ("No Product Feature Change", result["validation"]["product_feature_added"] is False),
        ("Artifacts Written", all(Path(path).exists() for path in artifacts.values())),
    ]
    print("NTPE 1.0 Stable Release Preparation Test")
    print("=" * 48)
    ok = True
    for name, passed in checks:
        print(f"{name:<28} {'PASS' if passed else 'FAIL'}")
        ok = ok and passed
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
