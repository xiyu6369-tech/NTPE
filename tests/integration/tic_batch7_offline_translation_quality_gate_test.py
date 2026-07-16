from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.shared.evidence import canonical_json_bytes, sha256_bytes
from core.translation_intelligence_corpus.offline_quality_gate import (
    FORMAL_INPUTS, _default_context, evaluate_regression_suite,
    evaluate_translation_candidate, validate_batch1_through_batch61_anchors,
    validate_untrusted_regression_records,
)
from core.translation_intelligence_corpus.quality_gate_models import TranslationCandidate
from core.translation_intelligence_corpus.quality_gate_report import build_batch7_payloads


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def file_sha(relative: str | Path) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


CONTEXT = _default_context()
SUBJECT = next(item for item in CONTEXT.regressions if item["category"] == "subject_reference_shift")
LEXICAL = next(item for item in CONTEXT.regressions if item["category"] == "lexical_choice")
VALIDATION = load("artifacts/tic_batch7/OFFLINE_QUALITY_GATE_VALIDATION.json")
STATISTICS = load("artifacts/tic_batch7/TIC_BATCH7_STATISTICS.json")
INDEX = load("artifacts/tic_batch7/OFFLINE_QUALITY_GATE_INDEX.json")
GATE = load("artifacts/tic_batch7/OFFLINE_TRANSLATION_QUALITY_GATE.json")
FIXTURES = load("artifacts/tic_batch7/OFFLINE_QUALITY_GATE_FIXTURES.json")
PERFORMANCE = load("artifacts/tic_batch7/OFFLINE_QUALITY_GATE_PERFORMANCE.json")
BATCH61_MANIFEST = load("manifests/tic_batch61_human_approval_regression_activation_manifest.json")


def evaluate(case, text):
    return evaluate_translation_candidate(source_text=case["source_text"], translation_text=text, applicable_regression_ids=(case["regression_id"],))


def test_01_batch1_through_batch61_anchor_sha_values_are_unchanged():
    anchors = validate_batch1_through_batch61_anchors(ROOT)
    assert anchors == VALIDATION["source_anchors"]
    assert all(file_sha(path) == digest for path, digest in anchors.items())


def test_02_two_active_regressions_are_loaded():
    assert len(CONTEXT.regressions) == 2
    assert all(item["regression_status"] == "active" for item in CONTEXT.regressions)


def test_03_applicability_is_not_global():
    result = evaluate_translation_candidate(source_text="인간", translation_text="相當理性的人")
    assert result.gate_status == "not_applicable"
    assert result.quality_candidate_allowed is False


def test_04_subject_bad_translation_fails():
    assert evaluate(SUBJECT, SUBJECT["bad_translation"]).gate_status == "fail"


def test_05_subject_approved_translation_passes():
    assert evaluate(SUBJECT, SUBJECT["approved_translation"]).gate_status == "pass"


def test_06_subject_unrelated_translation_does_not_pass():
    assert evaluate(SUBJECT, "完全無關的固定測試句子。").gate_status == "fail"


def test_07_lexical_bad_translation_fails():
    assert evaluate(LEXICAL, LEXICAL["bad_translation"]).gate_status == "fail"


def test_08_lexical_approved_translation_passes():
    assert evaluate(LEXICAL, LEXICAL["approved_translation"]).gate_status == "pass"


def test_09_lexical_unrelated_translation_does_not_pass():
    assert evaluate(LEXICAL, "完全無關的人。").gate_status == "fail"


def test_10_unrelated_candidate_is_not_applicable():
    result = evaluate_translation_candidate(source_text="고정 사례가 아니다.", translation_text="不是固定案例。")
    assert result.gate_status == "not_applicable"


def test_11_not_applicable_never_allows_quality_candidate():
    result = evaluate_translation_candidate(source_text="고정 사례가 아니다.", translation_text="不是固定案例。")
    assert result.quality_candidate_allowed is result.review_ready is result.regression_safe is False


def test_12_empty_translation_is_invalid_input():
    assert evaluate(SUBJECT, "").gate_status == "invalid_input"


def test_13_tampered_regression_sha_fails_closed():
    regressions = [dict(item) for item in load("artifacts/tic_batch61/ACTIVE_TRANSLATION_QUALITY_REGRESSIONS.json")["items"]]
    regressions[0]["approved_translation_sha256"] = "0" * 64
    valid, reasons = validate_untrusted_regression_records(regressions=tuple(regressions), approvals=tuple(load("artifacts/tic_batch61/HUMAN_APPROVAL_RECORDS.json")["items"]))
    assert valid is False and "tampered_regression_integrity" in reasons


def test_14_missing_approval_fails_closed():
    regressions = tuple(load("artifacts/tic_batch61/ACTIVE_TRANSLATION_QUALITY_REGRESSIONS.json")["items"])
    valid, reasons = validate_untrusted_regression_records(regressions=regressions, approvals=())
    assert valid is False and "missing_human_approval" in reasons


def test_15_defect_blocking_preserves_original_value():
    assert all(item["defect_blocking"] is False for item in CONTEXT.regressions)


def test_16_regression_gate_blocking_is_separate_and_true():
    assert all(item["regression_gate_blocking"] is True for item in CONTEXT.regressions)


def test_17_candidate_is_immutable_and_input_metadata_is_copied():
    metadata = {"alignment_id": SUBJECT["alignment_id"]}
    candidate = TranslationCandidate("C", SUBJECT["source_text"], SUBJECT["approved_translation"], metadata=metadata)
    metadata["alignment_id"] = "changed"
    assert candidate.metadata["alignment_id"] == SUBJECT["alignment_id"]
    with pytest.raises(FrozenInstanceError):
        candidate.source_text = "changed"  # type: ignore[misc]


def test_18_gate_is_deterministic():
    first = evaluate(SUBJECT, SUBJECT["approved_translation"]).as_dict()
    second = evaluate(SUBJECT, SUBJECT["approved_translation"]).as_dict()
    assert first == second and VALIDATION["deterministic"] is True


def test_19_provider_requests_are_zero():
    assert VALIDATION["provider_requests"] == 0
    assert all(item["provider_executed"] is False for item in VALIDATION["validation_results"])


def test_20_network_requests_are_zero():
    assert VALIDATION["network_requests"] == 0


def test_21_disk_writes_during_evaluation_are_zero():
    assert VALIDATION["disk_writes"] == 0
    assert evaluate(SUBJECT, SUBJECT["approved_translation"]).disk_writes == 0


def test_22_runtime_stages_are_zero():
    assert VALIDATION["runtime_stages"] == 0


def test_23_prompt_tokens_delta_is_zero():
    manifest = load("manifests/tic_batch7_offline_translation_quality_gate_manifest.json")
    assert manifest["boundary"]["prompt_tokens_added"] == 0


def test_24_performance_gate_passes():
    assert PERFORMANCE["performance_gate_pass"] is True
    assert PERFORMANCE["median_timings"]["single_candidate_median_ms"] < 2
    assert PERFORMANCE["median_timings"]["two_regression_suite_median_ms"] < 5
    assert PERFORMANCE["median_timings"]["one_hundred_candidate_batch_median_ms"] < 250


def test_25_index_is_complete():
    required = {"regression_id", "failure_case_id", "category", "case_id", "alignment_id", "evaluation_type", "regression_gate_blocking", "defect_blocking", "applicability_type", "gate_status"}
    assert len(INDEX["items"]) == 2 and all(required <= set(item) for item in INDEX["items"])


def test_26_statistics_are_consistent():
    assert STATISTICS["active_regressions_loaded"] == 2
    assert STATISTICS["gate_fixtures"] == 9
    assert STATISTICS["historical_bad_fail_count"] == 2
    assert STATISTICS["human_approved_pass_count"] == 2
    assert STATISTICS["unrelated_candidate_rejected_count"] >= 3
    assert STATISTICS["quality_candidates_allowed"] == 2
    assert STATISTICS["quality_candidates_blocked"] == 7


def test_27_manifest_sha_values_are_correct():
    manifest = load("manifests/tic_batch7_offline_translation_quality_gate_manifest.json")
    assert all(file_sha(path) == digest for path, digest in manifest["files"].items())
    assert manifest["source_anchors"] == VALIDATION["source_anchors"]


def test_28_historical_translation_sha_values_are_unchanged():
    for case in load("artifacts/tic_batch2/TRANSLATION_CASES.json")["translation_cases"]:
        assert file_sha(case["translation_file"]) == case["translation_sha256"]


def test_29_production_is_not_modified_or_connected():
    assert GATE["production_boundary"]["production_connected"] is False
    assert GATE["production_boundary"]["runtime_connected"] is False


def test_30_provider_is_not_executed_or_connected():
    assert GATE["provider_boundary"]["provider_connected"] is False
    assert GATE["provider_boundary"]["provider_requests"] == 0


def test_31_no_new_translation_is_generated():
    manifest = load("manifests/tic_batch7_offline_translation_quality_gate_manifest.json")
    assert manifest["boundary"]["new_translation_generated"] is False


def test_32_tic_batch8_has_not_started():
    manifest = load("manifests/tic_batch7_offline_translation_quality_gate_manifest.json")
    assert manifest["boundary"]["tic_batch8_started"] is False


def test_gate_api_is_keyword_only():
    with pytest.raises(TypeError):
        evaluate_translation_candidate(SUBJECT["source_text"], SUBJECT["approved_translation"])  # type: ignore[misc]


def test_explicit_source_mismatch_is_insufficient_evidence():
    result = evaluate_translation_candidate(source_text="다른 원문", translation_text=SUBJECT["approved_translation"], applicable_regression_ids=(SUBJECT["regression_id"],))
    assert result.gate_status == "insufficient_evidence" and result.quality_candidate_allowed is False


def test_suite_api_evaluates_immutable_candidates():
    candidates = (
        TranslationCandidate("S", SUBJECT["source_text"], SUBJECT["approved_translation"], case_id=SUBJECT["case_id"], failure_case_id=SUBJECT["failure_case_id"], metadata={"alignment_id": SUBJECT["alignment_id"]}),
        TranslationCandidate("L", LEXICAL["source_text"], LEXICAL["approved_translation"], case_id=LEXICAL["case_id"], failure_case_id=LEXICAL["failure_case_id"], metadata={"alignment_id": LEXICAL["alignment_id"]}),
    )
    result = evaluate_regression_suite(candidates=candidates)
    assert result.total_candidates == 2 and result.pass_count == 2 and result.all_regression_safe is True


def test_fixture_inventory_contains_all_nine_required_cases():
    assert len(FIXTURES["items"]) == 9
    assert {item["kind"] for item in FIXTURES["items"]} >= {"historical_bad", "human_approved", "unrelated_translation", "unrelated_source", "invalid_input", "tampered_regression"}


def test_batch61_formal_inputs_remain_byte_identical():
    assert all(file_sha(path) == BATCH61_MANIFEST["files"][Path(path).as_posix()] for path in FORMAL_INPUTS)


def test_artifact_build_is_deterministic_and_canonical():
    first = build_batch7_payloads(ROOT)
    second = build_batch7_payloads(ROOT)
    assert first == second
    for relative, payload in first.items():
        assert canonical_json_bytes(payload) == (ROOT / relative).read_bytes()


def test_gate_integrity_is_valid():
    body = {key: value for key, value in GATE.items() if key != "integrity"}
    assert GATE["integrity"]["payload_sha256"] == sha256_bytes(canonical_json_bytes(body))
