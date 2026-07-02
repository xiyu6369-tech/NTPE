from __future__ import annotations

from typing import Dict, Any

from .baseline import get_foundation_baseline, is_foundation_frozen
from .manifest import get_foundation_manifest, validate_foundation_manifest
from .compatibility import build_compatibility_report
from .regression import run_foundation_regression


def run_foundation_acceptance() -> Dict[str, Any]:
    baseline = get_foundation_baseline().to_dict()
    manifest = get_foundation_manifest()
    compatibility = build_compatibility_report()
    regression = run_foundation_regression()
    passed = (
        is_foundation_frozen()
        and validate_foundation_manifest(manifest)
        and compatibility.get("passed")
        and regression.get("passed")
    )
    return {
        "passed": bool(passed),
        "baseline": baseline,
        "manifest": manifest,
        "compatibility": compatibility,
        "regression": regression,
    }
