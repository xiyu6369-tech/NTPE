from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.shared.evidence import canonical_json_bytes, sha256_bytes, sha256_text
from core.translation_intelligence_corpus.correction_records import (
    validate_batch1_through_batch5_anchors,
)
from core.translation_intelligence_corpus.quality_regression import (
    build_batch6_payloads,
    evaluate_regression_case,
)


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def file_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


BATCH2_CASES = load("artifacts/tic_batch2/TRANSLATION_CASES.json")["translation_cases"]
BATCH4 = load("artifacts/tic_batch4/HUMAN_CONFIRMED_FAILURE_CORPUS.json")
BATCH5 = load("artifacts/tic_batch5/HUMAN_CONFIRMED_FAILURE_CORPUS_V2.json")
CORRECTIONS = load("artifacts/tic_batch6/HUMAN_CORRECTION_RECORDS.json")
ROOT_CAUSES = load("artifacts/tic_batch6/ROOT_CAUSE_RECORDS.json")
REGRESSIONS = load("artifacts/tic_batch6/TRANSLATION_QUALITY_REGRESSION_CASES.json")
VALIDATION = load("artifacts/tic_batch6/QUALITY_REGRESSION_VALIDATION.json")
STATISTICS = load("artifacts/tic_batch6/TIC_BATCH6_STATISTICS.json")
INDEX = load("artifacts/tic_batch6/QUALITY_REGRESSION_INDEX.json")


def by_category(payload, category):
    return next(item for item in payload["items"] if item.get("category", item.get("failure_category")) == category)


def test_batch1_through_batch5_anchor_sha_values_are_unchanged():
    anchors = validate_batch1_through_batch5_anchors(ROOT)
    assert anchors == VALIDATION["source_anchors"]
    assert all(file_sha(path) == digest for path, digest in anchors.items())


def test_batch4_to_batch5_failure_chain_is_preserved():
    assert canonical_json_bytes(BATCH5["failure_cases"][0]) == canonical_json_bytes(BATCH4["failure_cases"][0])
    assert len(BATCH5["failure_cases"]) == 2


def test_only_the_two_frozen_failure_cases_are_processed():
    expected = {item["failure_case_id"] for item in BATCH5["failure_cases"]}
    assert expected == {item["failure_case_id"] for item in CORRECTIONS["items"]}
    assert expected == {item["failure_case_id"] for item in ROOT_CAUSES["items"]}
    assert expected == {item["failure_case_id"] for item in REGRESSIONS["items"]}


def test_corrections_preserve_source_and_original_translation():
    failures = {item["failure_case_id"]: item for item in BATCH5["failure_cases"]}
    for correction in CORRECTIONS["items"]:
        failure = failures[correction["failure_case_id"]]
        assert correction["source_text"] == failure["source_text"]
        assert correction["original_translation"] == failure["translation_text"]


def test_subject_correction_is_minimal_and_actor_bounded():
    item = next(
        x
        for x in CORRECTIONS["items"]
        if x["failure_case_id"] == "TIC-FAIL-B4-FAA4C8AD021D6103DDA6"
    )
    assert item["corrected_translation"] == "被拋在遠方的那個男人雖然像個怪物，但至少他仍然是個理智清醒的人，他也會明白這種情況不可能是鄭泰義故意製造的。"
    assert "鄭泰義也明白" not in item["corrected_translation"]


def test_lexical_correction_changes_only_the_confirmed_term():
    item = next(x for x in CORRECTIONS["items"] if x["source_text"] == "인간")
    assert item["original_translation"] == "相當理性的人間"
    assert item["corrected_translation"] == "相當理性的人"


def test_correction_provenance_is_complete():
    for item in CORRECTIONS["items"]:
        assert item["human_provenance"]["complete"] is True
        assert item["human_provenance"]["semantic_constraint_supplied"] is True
        assert item["review_reason"] and item["source_references"]


def test_no_codex_draft_is_marked_human_approved():
    assert all(item["correction_status"] == "human_draft" for item in CORRECTIONS["items"])
    assert all(item["approved_at"] is None for item in CORRECTIONS["items"])
    assert all(item["human_provenance"]["exact_wording_human_approved"] is False for item in CORRECTIONS["items"])


def test_root_causes_are_evidence_supported_not_confirmed():
    assert all(item["root_cause_status"] == "evidence_supported" for item in ROOT_CAUSES["items"])
    assert not any(item["root_cause_status"] == "human_confirmed" for item in ROOT_CAUSES["items"])


def test_subject_root_cause_distinguishes_all_required_layers():
    item = next(x for x in ROOT_CAUSES["items"] if x["failure_category"] == "subject_reference_shift")
    assert set(item["evidence"]["layer_assessment"]) == {"prompt", "context", "model_output", "post_processing", "QA_detection"}
    assert any(cause["cause"] == "long_distance_subject_resolution_risk" for cause in item["secondary_root_causes"])


def test_lexical_root_cause_covers_disambiguation_and_validation():
    item = next(x for x in ROOT_CAUSES["items"] if x["failure_category"] == "lexical_choice")
    causes = {cause["cause"] for cause in item["secondary_root_causes"]}
    assert "korean_chinese_near_form_lexical_selection_risk" in causes
    assert "traditional_chinese_lexical_validation_gap" in causes


def test_recommended_fix_locations_are_minimal_and_present():
    assert {item["recommended_fix_location"] for item in ROOT_CAUSES["items"]} == {"semantic regression", "lexical validator"}
    assert all("runtime" in item["non_fix_locations"] and "provider" in item["non_fix_locations"] for item in ROOT_CAUSES["items"])


def test_subject_bad_translation_fails():
    case = by_category(REGRESSIONS, "subject_reference_shift")
    result = evaluate_regression_case(case, case["bad_translation"])
    assert result["accepted"] is False
    assert result["checks"]["jeong_is_not_cognitive_actor"] is False


def test_subject_draft_passes_constraints_but_remains_pending():
    case = by_category(REGRESSIONS, "subject_reference_shift")
    assert evaluate_regression_case(case, case["draft_translation"])["accepted"] is True
    assert case["approved_translation"] is None
    assert case["regression_status"] == "pending_human_correction"


def test_lexical_bad_translation_fails():
    case = by_category(REGRESSIONS, "lexical_choice")
    result = evaluate_regression_case(case, case["bad_translation"])
    assert result["accepted"] is False
    assert result["checks"]["forbidden_phrase_absent"] is False


def test_lexical_draft_passes_constraints_but_remains_pending():
    case = by_category(REGRESSIONS, "lexical_choice")
    assert evaluate_regression_case(case, case["draft_translation"])["accepted"] is True
    assert case["approved_translation"] is None
    assert case["regression_status"] == "pending_human_correction"


def test_unrelated_translation_is_never_accepted():
    unrelated = "完全無關的句子。"
    assert all(evaluate_regression_case(item, unrelated)["accepted"] is False for item in REGRESSIONS["items"])


def test_lexical_evaluator_is_case_bound_not_a_global_replacement():
    case = by_category(REGRESSIONS, "lexical_choice")
    assert case["semantic_constraints"]["global_replacement_rule"] is False
    assert evaluate_regression_case(case, "理性的人")["accepted"] is False
    assert evaluate_regression_case(case, "人")["accepted"] is False


def test_evaluator_fails_closed_for_unknown_or_empty_input():
    assert REGRESSIONS["supported_evaluation_types"] == [
        "exact_constraint",
        "forbidden_phrase",
        "required_semantic_actor",
        "lexical_choice",
    ]
    assert evaluate_regression_case({"category": "unknown"}, "文字")["accepted"] is False
    assert evaluate_regression_case(REGRESSIONS["items"][0], "")["accepted"] is False


def test_regression_build_is_deterministic_and_canonical():
    first = build_batch6_payloads(ROOT)
    second = build_batch6_payloads(ROOT)
    assert first == second
    for relative, payload in first.items():
        assert canonical_json_bytes(payload) == (ROOT / relative).read_bytes()


def test_validation_records_bad_fail_draft_pass_and_pending_approval():
    assert VALIDATION["all_bad_translations_fail"] is True
    assert VALIDATION["all_unrelated_translations_rejected"] is True
    assert VALIDATION["deterministic"] is True
    assert all(item["approved_translation_passes"] is None for item in VALIDATION["items"])
    assert all(item["draft_translation_satisfies_constraints"] is True for item in VALIDATION["items"])


def test_statistics_are_consistent():
    assert STATISTICS["failure_cases_processed"] == 2
    assert STATISTICS["human_approved_corrections"] == 0
    assert STATISTICS["human_draft_corrections"] == 2
    assert STATISTICS["root_causes_evidence_supported"] == 2
    assert STATISTICS["regression_cases_created"] == 2
    assert STATISTICS["regression_cases_active"] == 0
    assert STATISTICS["regression_cases_pending"] == 2
    assert STATISTICS["bad_translation_fail_count"] == 2
    assert STATISTICS["approved_translation_pass_count"] == 0


def test_index_is_complete():
    required = {"regression_id", "failure_case_id", "failure_category", "root_cause_status", "affected_layer", "recommended_fix_location", "correction_status", "regression_status", "blocking"}
    assert len(INDEX["items"]) == 2
    assert all(required <= set(item) for item in INDEX["items"])


def test_record_integrity_hashes_are_valid():
    for payload in (CORRECTIONS, ROOT_CAUSES, REGRESSIONS, VALIDATION):
        for item in payload["items"]:
            body = {key: value for key, value in item.items() if key != "integrity"}
            assert item["integrity"]["payload_sha256"] == sha256_bytes(canonical_json_bytes(body))
    for correction in CORRECTIONS["items"]:
        assert correction["corrected_translation_sha256"] == sha256_text(correction["corrected_translation"])


def test_manifest_sha256_values_are_correct():
    manifest = load("manifests/tic_batch6_human_correction_root_cause_regression_manifest.json")
    assert all(file_sha(path) == digest for path, digest in manifest["files"].items())
    assert manifest["source_anchors"] == VALIDATION["source_anchors"]


def test_historical_translation_sha_values_are_unchanged():
    checked = set()
    for case in BATCH2_CASES:
        if case["translation_file"] not in checked:
            assert file_sha(case["translation_file"]) == case["translation_sha256"]
            checked.add(case["translation_file"])


def test_no_provider_runtime_prompt_or_qa_engine_imports_or_changes():
    boundary = VALIDATION["boundary"]
    for key in ("provider_executed", "runtime_modified", "provider_modified", "prompt_modified", "qa_engine_modified", "stage11_modified", "stage12_modified"):
        assert boundary[key] is False
    for name in ("correction_records.py", "root_cause_records.py", "quality_regression.py"):
        text = (ROOT / "core/translation_intelligence_corpus" / name).read_text(encoding="utf-8")
        imports = [line.lower() for line in text.splitlines() if line.startswith(("import ", "from "))]
        assert not any(word in line for line in imports for word in ("runtime", "provider", "prompt", "requests", "http", "llm"))


def test_boundary_declares_no_production_fix_quality_claim_or_batch7():
    boundary = VALIDATION["boundary"]
    assert boundary["network_requests"] == 0
    assert boundary["new_translation_generated"] is False
    assert boundary["historical_translation_modified"] is False
    assert boundary["failure_corpus_v2_modified"] is False
    assert boundary["production_fix_applied"] is False
    assert boundary["translation_quality_improved"] is False
    assert boundary["translation_quality_regression_guard_created"] is True
    assert boundary["tic_batch7_started"] is False
