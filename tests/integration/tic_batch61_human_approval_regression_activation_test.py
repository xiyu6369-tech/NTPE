from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.shared.evidence import canonical_json_bytes, sha256_bytes, sha256_text
from core.translation_intelligence_corpus.human_approval import (
    APPROVED_TRANSLATIONS,
    FORMAL_BATCH6_INPUTS,
    validate_batch1_through_batch6_anchors,
)
from core.translation_intelligence_corpus.regression_activation import (
    UNRELATED_TRANSLATION,
    build_batch61_payloads,
    evaluate_active_regression,
)


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def file_sha(relative: str | Path) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


BATCH2_CASES = load("artifacts/tic_batch2/TRANSLATION_CASES.json")["translation_cases"]
BATCH6_MANIFEST = load("manifests/tic_batch6_human_correction_root_cause_regression_manifest.json")
BATCH6_CORRECTIONS = load("artifacts/tic_batch6/HUMAN_CORRECTION_RECORDS.json")
BATCH6_ROOTS = load("artifacts/tic_batch6/ROOT_CAUSE_RECORDS.json")
BATCH6_REGRESSIONS = load("artifacts/tic_batch6/TRANSLATION_QUALITY_REGRESSION_CASES.json")
APPROVALS = load("artifacts/tic_batch61/HUMAN_APPROVAL_RECORDS.json")
CORRECTIONS_V2 = load("artifacts/tic_batch61/HUMAN_CORRECTION_RECORDS_V2.json")
ACTIVE = load("artifacts/tic_batch61/ACTIVE_TRANSLATION_QUALITY_REGRESSIONS.json")
VALIDATION = load("artifacts/tic_batch61/ACTIVE_REGRESSION_VALIDATION.json")
STATISTICS = load("artifacts/tic_batch61/TIC_BATCH61_STATISTICS.json")
INDEX = load("artifacts/tic_batch61/ACTIVE_REGRESSION_INDEX.json")


def by_category(payload, category):
    return next(item for item in payload["items"] if item.get("category", item.get("failure_category")) == category)


def test_01_batch1_through_batch6_anchor_sha_values_are_unchanged():
    anchors = validate_batch1_through_batch6_anchors(ROOT)
    assert anchors == VALIDATION["source_anchors"] == APPROVALS["source_anchors"]
    assert all(file_sha(path) == digest for path, digest in anchors.items())


def test_02_approval_records_count_is_two():
    assert len(APPROVALS["items"]) == 2


def test_03_both_approvals_have_explicit_human_provenance():
    for item in APPROVALS["items"]:
        assert item["approval_status"] == "human_approved"
        assert item["reviewer_type"] == "human"
        assert item["human_provenance"] == "explicit_user_approval"


def test_04_approved_wording_matches_the_user_directive_exactly():
    assert {item["approved_translation"] for item in APPROVALS["items"]} == set(APPROVED_TRANSLATIONS.values())


def test_05_draft_wording_was_promoted_without_rewriting():
    old = {item["correction_id"]: item for item in BATCH6_CORRECTIONS["items"]}
    for item in CORRECTIONS_V2["items"]:
        assert item["corrected_translation"] == old[item["correction_id"]]["corrected_translation"]
        assert item["original_translation"] == old[item["correction_id"]]["original_translation"]


def test_06_correction_v2_records_are_human_approved():
    assert all(item["correction_status"] == "human_approved" for item in CORRECTIONS_V2["items"])
    assert all(item["exact_wording_human_approved"] is True for item in CORRECTIONS_V2["items"])
    assert all(item["approval_id"] and item["approval_source"] for item in CORRECTIONS_V2["items"])


def test_07_batch6_formal_artifacts_are_byte_preserved():
    assert all(file_sha(path) == BATCH6_MANIFEST["files"][Path(path).as_posix()] for path in FORMAL_BATCH6_INPUTS)


def test_08_root_cause_status_was_not_promoted():
    assert all(item["root_cause_status"] == "evidence_supported" for item in BATCH6_ROOTS["items"])
    assert not any(item["root_cause_status"] == "human_confirmed" for item in BATCH6_ROOTS["items"])


def test_09_exactly_two_regressions_are_active():
    assert len(ACTIVE["items"]) == 2
    assert all(item["regression_status"] == "active" for item in ACTIVE["items"])


def test_10_no_regressions_remain_pending():
    assert STATISTICS["pending_regressions"] == 0


def test_11_bad_subject_translation_fails():
    case = by_category(ACTIVE, "subject_reference_shift")
    result = evaluate_active_regression(case, case["bad_translation"])
    assert result["accepted"] is False
    assert result["checks"]["jeong_is_not_cognitive_actor"] is False


def test_12_approved_subject_translation_passes():
    case = by_category(ACTIVE, "subject_reference_shift")
    result = evaluate_active_regression(case, case["approved_translation"])
    assert result["accepted"] is True
    assert all(result["checks"].values())


def test_13_unrelated_subject_translation_is_not_approved():
    case = by_category(ACTIVE, "subject_reference_shift")
    assert evaluate_active_regression(case, UNRELATED_TRANSLATION)["accepted"] is False
    assert evaluate_active_regression(case, "鄭泰義不可能故意製造這種情況。") ["accepted"] is False


def test_14_bad_lexical_translation_fails():
    case = by_category(ACTIVE, "lexical_choice")
    result = evaluate_active_regression(case, case["bad_translation"])
    assert result["accepted"] is False
    assert result["checks"]["forbidden_phrase_absent"] is False


def test_15_approved_lexical_translation_passes():
    case = by_category(ACTIVE, "lexical_choice")
    assert evaluate_active_regression(case, case["approved_translation"])["accepted"] is True


def test_16_lexical_check_is_case_local_not_global_replace():
    case = by_category(ACTIVE, "lexical_choice")
    assert case["semantic_constraints"]["global_replacement_rule"] is False
    assert evaluate_active_regression(case, "人")["accepted"] is False
    assert evaluate_active_regression(case, "另一個人間")["accepted"] is False


def test_17_approved_translation_sha_values_are_correct_and_equal():
    approval_map = {item["failure_case_id"]: item for item in APPROVALS["items"]}
    for case in ACTIVE["items"]:
        expected = sha256_text(case["approved_translation"])
        assert case["approved_translation_sha256"] == expected
        assert approval_map[case["failure_case_id"]]["approved_translation_sha256"] == expected


def test_18_approval_ids_and_payload_rerun_are_deterministic():
    first = build_batch61_payloads(ROOT, APPROVALS["approved_at"])
    second = build_batch61_payloads(ROOT, APPROVALS["approved_at"])
    assert first == second
    rebuilt = first["artifacts/tic_batch61/HUMAN_APPROVAL_RECORDS.json"]
    assert [item["approval_id"] for item in rebuilt["items"]] == [item["approval_id"] for item in APPROVALS["items"]]


def test_19_active_regression_index_is_complete():
    required = {"regression_id", "failure_case_id", "approval_id", "correction_id", "failure_category", "evaluation_type", "regression_status", "review_status", "blocking"}
    assert len(INDEX["items"]) == 2
    assert all(required <= set(item) for item in INDEX["items"])


def test_20_statistics_are_consistent():
    assert STATISTICS == {
        "schema_version": "tic.batch61.statistics.v1",
        "approvals_created": 2,
        "human_approved_corrections": 2,
        "active_regressions": 2,
        "pending_regressions": 0,
        "failure_categories": {"lexical_choice": 1, "subject_reference_shift": 1},
        "bad_translation_fail_count": 2,
        "approved_translation_pass_count": 2,
        "unrelated_translation_rejected_count": 2,
        "production_fixes_applied": 0,
        "root_causes_modified": 0,
    }


def test_21_manifest_sha_values_are_correct():
    manifest = load("manifests/tic_batch61_human_approval_regression_activation_manifest.json")
    assert all(file_sha(path) == digest for path, digest in manifest["files"].items())
    assert manifest["source_anchors"] == VALIDATION["source_anchors"]


def test_22_historical_translation_sha_values_are_unchanged():
    checked = set()
    for case in BATCH2_CASES:
        if case["translation_file"] not in checked:
            assert file_sha(case["translation_file"]) == case["translation_sha256"]
            checked.add(case["translation_file"])


def _module_imports(name: str) -> list[str]:
    text = (ROOT / "core/translation_intelligence_corpus" / name).read_text(encoding="utf-8")
    return [line.lower() for line in text.splitlines() if line.startswith(("import ", "from "))]


def test_23_runtime_is_not_imported_or_modified():
    assert VALIDATION["boundary"]["runtime_modified"] is False
    assert not any("runtime" in line for name in ("human_approval.py", "regression_activation.py") for line in _module_imports(name))


def test_24_provider_is_not_imported_or_modified():
    assert VALIDATION["boundary"]["provider_modified"] is False
    assert not any(word in line for name in ("human_approval.py", "regression_activation.py") for line in _module_imports(name) for word in ("provider", "requests", "http", "llm"))


def test_25_prompt_is_not_imported_or_modified():
    assert VALIDATION["boundary"]["prompt_modified"] is False
    assert not any("prompt" in line for name in ("human_approval.py", "regression_activation.py") for line in _module_imports(name))


def test_26_qa_engine_is_not_imported_or_modified():
    assert VALIDATION["boundary"]["qa_engine_modified"] is False
    assert not any("qa" in line for name in ("human_approval.py", "regression_activation.py") for line in _module_imports(name))


def test_27_provider_was_not_executed():
    assert VALIDATION["provider_executed"] is False
    assert VALIDATION["boundary"]["network_requests"] == 0


def test_28_no_new_translation_was_generated():
    assert VALIDATION["boundary"]["new_translation_generated"] is False
    assert VALIDATION["boundary"]["historical_translation_modified"] is False


def test_29_no_production_fix_was_applied():
    assert VALIDATION["production_modified"] is False
    assert VALIDATION["boundary"]["production_fix_applied"] is False
    assert VALIDATION["boundary"]["translation_quality_improved"] is False


def test_30_tic_batch7_has_not_started():
    assert VALIDATION["boundary"]["tic_batch7_started"] is False
    assert VALIDATION["boundary"]["fixed_case_regression_protection_created"] is True


def test_record_integrity_hashes_are_valid():
    for payload in (APPROVALS, CORRECTIONS_V2, ACTIVE):
        for item in payload["items"]:
            body = {key: value for key, value in item.items() if key != "integrity"}
            assert item["integrity"]["payload_sha256"] == sha256_bytes(canonical_json_bytes(body))
