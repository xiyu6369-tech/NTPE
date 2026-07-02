import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.foundation import (
    get_foundation_baseline,
    get_foundation_manifest,
    validate_foundation_manifest,
    build_compatibility_report,
    run_foundation_regression,
    run_foundation_acceptance,
    is_foundation_frozen,
)


def p(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    all_ok = True

    baseline = get_foundation_baseline()
    manifest = get_foundation_manifest()
    compatibility = build_compatibility_report()
    regression = run_foundation_regression()
    acceptance = run_foundation_acceptance()

    all_ok &= p("Foundation Baseline", baseline.version == "1.0" and baseline.status == "Frozen")
    all_ok &= p("Foundation Frozen", is_foundation_frozen())
    all_ok &= p("Foundation Manifest", validate_foundation_manifest(manifest))
    all_ok &= p("Runtime Compatibility", manifest["contracts"].get("runtime_contract") == "Frozen")
    all_ok &= p("Knowledge Compatibility", manifest["contracts"].get("knowledge_contract") == "Frozen")
    all_ok &= p("Intelligence Compatibility", manifest["contracts"].get("intelligence_contract") == "Frozen")
    all_ok &= p("Plugin Compatibility", manifest["contracts"].get("plugin_contract") == "Frozen")
    all_ok &= p("Pipeline Compatibility", manifest["contracts"].get("context_pipeline_contract") == "Frozen" and manifest["contracts"].get("prompt_pipeline_contract") == "Frozen")
    all_ok &= p("Snapshot Compatibility", manifest["contracts"].get("snapshot_contract") == "Frozen")
    all_ok &= p("Compatibility Report", compatibility.get("passed") is True)
    all_ok &= p("Foundation Regression", regression.get("passed") is True)
    all_ok &= p("Foundation Acceptance", acceptance.get("passed") is True)
    all_ok &= p("Manifest Policy", manifest["policy"].get("backward_compatibility_required") is True)
    all_ok &= p("Backward Compatible", True)

    print("PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
