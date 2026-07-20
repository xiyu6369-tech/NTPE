from __future__ import annotations

import json

from tools.generate_te_v720_stage1258a_candidate_structural_failure_sealing import build_artifacts


def test_stage1258a_integration_seals_failure_and_root_cause_without_execution() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    historical = artifacts["historical_execution_seal.json"]
    assert historical["execution_status"] == "completed"
    assert historical["failure_reasons"] == ["hangul_residual", "bilingual_layout"]
    classification = artifacts["structural_failure_classification.json"]
    assert classification["structural_failure_class"] == "mixed_language_inline_output"
    assert classification["failure_subtype"] == "inline_hangul_name_residual"
    remediation = artifacts["remediation_decision.json"]
    assert remediation["remediation_class"] == "multiple_contributing_causes"
    assert remediation["prompt_change_authorized"] is False
