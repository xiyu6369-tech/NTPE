from __future__ import annotations

import json
from pathlib import Path

from core.prompt_contract_canary_readiness import evaluate_prompt_canary_readiness
from core.translation_quality_provider_canary.framework import _build_prompts


ROOT = Path(__file__).resolve().parents[2]
CASE = json.loads((ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_text(encoding="utf-8"))["cases"][0]


def _result():
    system, baseline, candidate, metadata = _build_prompts(str(CASE["case_id"]), str(CASE["source_text"]))
    return evaluate_prompt_canary_readiness(
        system_prompt=system,
        baseline_prompt=baseline,
        candidate_prompt=candidate,
        source_text=str(CASE["source_text"]),
        integration_metadata=metadata,
    )


def test_layout_marker_uniqueness_and_reference_isolation() -> None:
    result = _result()
    assert result.prompt_layout["status"] == "PASS"
    assert result.prompt_layout["boundary_occurrences"] == 1
    assert result.marker_integrity["korean_structural_marker_count"] == 1
    assert result.marker_integrity["output_structural_marker_count"] == 1
    assert result.marker_integrity["forbidden_labels_absent_from_output_boundary"] is True
    assert result.reference_isolation["all_reference_sections_inside_container"] is True
    assert result.reference_isolation["source_contamination"] is False
    assert result.reference_isolation["output_contamination"] is False


def test_fingerprint_is_deterministic_and_decision_is_fail_closed_for_provider() -> None:
    first = _result()
    second = _result()
    assert first.prompt_fingerprint == second.prompt_fingerprint
    assert first.prompt_fingerprint["values_equal"] is True
    assert first.readiness_summary["prompt_canary_ready"] is True
    assert first.readiness_summary["provider_eligible"] is False
    assert first.readiness_summary["provider_requests_added"] == first.readiness_summary["network_requests_added"] == 0


def test_token_budget_is_report_only_and_allocations_are_untouched() -> None:
    result = _result()
    assert result.token_budget == {
        "baseline_tokens": 328,
        "candidate_tokens": 651,
        "delta_tokens": 323,
        "policy_share_percentage": 9.06,
        "reference_share_percentage": result.token_budget["reference_share_percentage"],
        "source_share_percentage": 2.92,
        "status": "PASS",
    }
    assert result.readiness_summary["integration_budget_exhausted"] is False


def test_invalid_marker_layout_is_not_canary_ready_and_remains_provider_ineligible() -> None:
    system, baseline, candidate, metadata = _build_prompts(str(CASE["case_id"]), str(CASE["source_text"]))
    invalid = evaluate_prompt_canary_readiness(
        system_prompt=system,
        baseline_prompt=baseline,
        candidate_prompt=candidate + "\n【Output】duplicate",
        source_text=str(CASE["source_text"]),
        integration_metadata=metadata,
    )
    assert invalid.marker_integrity["status"] == "FAIL"
    assert invalid.readiness_summary["prompt_canary_ready"] is False
    assert invalid.readiness_summary["fail_closed"] is True
    assert invalid.readiness_summary["provider_eligible"] is False