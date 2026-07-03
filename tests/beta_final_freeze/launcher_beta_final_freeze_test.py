from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packaging.beta_final_freeze import build_beta_final_freeze, load_beta_final_freeze


def check(label, condition):
    print(f"{label:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    print("NTPE 1.0 Beta Final Freeze / RC Preparation Test")
    print("=" * 58)
    result = build_beta_final_freeze(ROOT)
    loaded = load_beta_final_freeze(result["manifest_path"])
    check("Beta Final Manifest", loaded["validation"]["valid"])
    check("Beta Final Status", loaded["status"] == "BETA_FINAL_FROZEN")
    check("RC Target", loaded["rc_target"] == "1.0.0-rc.1")
    check("Frozen Components", loaded["validation"]["component_count"] >= 10)
    check("RC Checks", all(loaded["rc_checks"].values()))
    check("Compatibility Policy", loaded["validation"]["compatibility"]["frozen_api_safe"])
    print("PASS")


if __name__ == "__main__":
    main()
