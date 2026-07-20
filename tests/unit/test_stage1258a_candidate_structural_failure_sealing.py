from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.generate_te_v720_stage1258a_candidate_structural_failure_sealing import (
    CLAIM, EXPECTED_CLAIM_SHA256, EXPECTED_RESPONSE_SHA256, RESPONSE,
    build_artifacts, classify_hangul_residuals,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "영희가 민수와 선생님을 번갈아 보며 말했다. ‘선생님, 민수 씨도 함께 가실까요?’"
OUTPUT = "「師傅，您也一起去嗎？」 영희問道，目光在民수和老師之間來回移動。"


def payloads() -> dict[str, dict[str, object]]:
    return {path.name: json.loads(data) for path, data in build_artifacts().items()}


def test_historical_claim_request_count_and_response_are_immutable() -> None:
    claim_before, response_before = CLAIM.read_bytes(), RESPONSE.read_bytes()
    result = payloads()
    assert hashlib.sha256(claim_before).hexdigest() == EXPECTED_CLAIM_SHA256
    assert hashlib.sha256(response_before).hexdigest() == EXPECTED_RESPONSE_SHA256
    assert CLAIM.read_bytes() == claim_before and RESPONSE.read_bytes() == response_before
    assert result["claim_lifecycle.json"]["actual_requests_consumed"] == 1
    assert result["claim_lifecycle.json"]["replay_allowed"] is False


def test_proper_name_residuals_are_separate_from_source_echo() -> None:
    result = classify_hangul_residuals(SOURCE, OUTPUT)
    assert result["observed_residuals"] == ["영희", "수"]
    assert result["full_korean_names_detected"] == ["영희"]
    assert result["partial_korean_syllable_residuals"] == ["수"]
    assert result["full_korean_source_echo"] is False
    assert result["partial_korean_source_echo"] is False
    assert result["korean_lexical_or_source_passage_echo"] is False
    assert result["hangul_proper_name_residual"] is True
    assert result["inline_mixed_language_output"] is True


def test_full_name_and_partial_syllable_detection() -> None:
    full = classify_hangul_residuals(SOURCE, "角色영희仍在場。")
    partial = classify_hangul_residuals(SOURCE, "角色民수仍在場。")
    assert full["full_korean_names_detected"] == ["영희"]
    assert partial["partial_korean_syllable_residuals"] == ["수"]


def test_root_cause_is_evidence_backed_and_does_not_invent_mapping() -> None:
    result = payloads()
    trace = result["name_resolution_trace.json"]
    names = {row["source_name"]: row for row in trace["name_evidence"]}
    assert names["영희"]["rendered_prompt_mapping"] == "Yeong-hui"
    assert names["영희"]["evidence_class"] == "mapping_present_provider_ignored"
    assert names["민수"]["expected_target_representation"] is None
    assert names["민수"]["unresolved"] is True
    prompt = result["prompt_name_mapping_evidence.json"]
    assert prompt["prompt_budget_exhausted"] is False
    assert prompt["invented_name_mappings"] == []


def test_no_response_repair_and_activation_gate_unchanged() -> None:
    result = payloads()
    assert result["name_resolution_trace.json"]["validation_detected_but_did_not_repair"] is True
    assert result["historical_execution_seal.json"]["activation_gate"] == (
        "translation_quality_integration_ready_for_controlled_canary"
    )
    assert result["historical_execution_seal.json"]["candidate_structural_pass"] is False


def test_sealing_generation_is_deterministic_and_secret_free() -> None:
    first, second = build_artifacts(), build_artifacts()
    assert first == second
    raw = b"".join(first.values()).lower()
    assert b"bearer " not in raw and b"x-api-key" not in raw and b"api_key" not in raw


def test_remediation_class_is_multiple_contributing_causes() -> None:
    decision = payloads()["remediation_decision.json"]
    assert decision["remediation_class"] == "multiple_contributing_causes"
    assert decision["contributing_classes"] == [
        "mapping_present_provider_ignored", "missing_name_mapping", "incomplete_name_normalization",
    ]
    assert decision["mapping_dropped_by_budget"] is False
    assert decision["provider_rerun_authorized"] is False
