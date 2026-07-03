"""Release candidate validator for RC.5."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

from .criteria import RCValidationBaseline


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ReleaseCandidateValidator:
    """Runs RC.5 validation without changing product behavior."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _artifact_presence(self) -> Dict[str, bool]:
        required = [
            "Regression_Report_RC_04.md",
            "Compatibility_Report_RC_04.md",
            "Performance_Report_RC_04.md",
            "Translation_Consistency_Audit_Report_RC_04.md",
            "Translation_Regression_Report_RC_04.md",
        ]
        return {name: (self.root / name).exists() or (self.root / "release" / name).exists() for name in required}

    def run(self) -> Dict[str, object]:
        baseline = RCValidationBaseline()
        baseline_dict = baseline.to_dict()
        validation = baseline.validate()
        artifacts = self._artifact_presence()
        artifacts_present = all(artifacts.values())
        passed = bool(validation["valid"] and artifacts_present)
        result = {
            "stage": "RC.5",
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "baseline": baseline_dict,
            "artifact_presence": artifacts,
            "validation": {
                **baseline.validation,
                **validation,
                "release_artifacts_present": artifacts_present,
                "rc_candidate_ready": passed,
            },
            "hashes": {
                "rc_validation_hash": stable_hash(baseline_dict),
                "artifact_presence_hash": stable_hash(artifacts),
                "release_candidate_hash": stable_hash({"baseline": baseline_dict, "artifacts": artifacts}),
            },
        }
        return result
