from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import core.translation_intelligence_corpus.failure_corpus as failure_module
from core.shared.evidence import canonical_json_bytes, sha256_bytes, sha256_text
from core.translation_intelligence_corpus.failure_corpus import (
    BATCH3_INPUTS,
    build_batch4_payloads,
    validate_source_anchors,
)

ROOT = Path(__file__).resolve().parents[2]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def file_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


CORPUS = load("artifacts/tic_batch4/HUMAN_CONFIRMED_FAILURE_CORPUS.json")
EXCLUDED = load("artifacts/tic_batch4/EXCLUDED_FAILURE_CANDIDATES.json")
STATISTICS = load("artifacts/tic_batch4/FAILURE_CORPUS_STATISTICS.json")
INDEX = load("artifacts/tic_batch4/FAILURE_CASE_INDEX.json")
FAILURES = CORPUS["failure_cases"]


def test_batch1_through_batch3_anchor_sha256_values_are_frozen():
    anchors = validate_source_anchors(ROOT)
    assert anchors == CORPUS["source_anchors"]
    assert all(file_sha(path) == digest for path, digest in anchors.items())


def test_initial_failure_corpus_contains_exactly_one_case():
    assert CORPUS["status"] == "active_initial_corpus"
    assert CORPUS["corpus_scope"] == "human-confirmed precise bilateral alignments only"
    assert len(FAILURES) == 1


def test_automatic_unknown_and_linked_but_not_aligned_evidence_are_excluded():
    reasons = {item["evidence_id"]: item["exclusion_reason"] for item in EXCLUDED["items"]}
    assert reasons["TIC-EVID-B3-EF8594197F5D82C674A0"] == "automatic_evidence_not_human_confirmed"
    assert reasons["TIC-EVID-B3-5A1E78336F76B1B5369A"] == "unknown_reviewer_and_incomplete_review"
    assert reasons["TIC-EVID-B3-4C47ECCEDCAB1775DE59"] == "missing_source_excerpt"
    assert {item["evidence_id"] for item in FAILURES}.isdisjoint(reasons)


def test_missing_source_excerpt_candidate_is_preserved_for_future_action():
    candidate = next(item for item in EXCLUDED["items"] if item["evidence_id"] == "TIC-EVID-B3-4C47ECCEDCAB1775DE59")
    assert candidate["current_status"] == "linked_but_not_aligned"
    assert "source_excerpt" in candidate["missing_requirements"]
    assert candidate["case_id"] == "TIC-CASE-B2-598DC16E43DB4363D420"


def test_failure_case_has_exact_bilateral_text_overlap_and_offsets():
    failure = FAILURES[0]
    assert failure["source_text"] and failure["translation_text"]
    assert failure["source_overlap"] == failure["translation_overlap"] == 1.0
    assert all(isinstance(failure[name], int) for name in ("source_start_offset", "source_end_offset", "translation_start_offset", "translation_end_offset"))
    assert sha256_text(failure["source_text"]) == failure["source_sha256"]
    assert sha256_text(failure["translation_text"]) == failure["translation_sha256"]


def test_failure_alignment_is_high_confidence_and_not_unilateral():
    failure = FAILURES[0]
    assert failure["alignment_confidence"] in {"exact", "high"}
    assert failure["alignment_type"] not in {"source_only", "translation_only", "unresolved"}


def test_failure_has_complete_human_provenance_and_traceable_ids():
    failure = FAILURES[0]
    assert failure["reviewer_type"] == "human"
    assert failure["human_provenance"]["complete"] is True
    assert failure["case_id"] and failure["alignment_id"] and failure["evidence_id"]
    assert failure["evidence_id"] == "TIC-EVID-B3-SUBJECT-SHIFT-001"


def test_subject_shift_case_is_unique_and_contains_exact_problem_excerpts():
    matches = [item for item in FAILURES if item["failure_category"] == "subject_reference_shift"]
    assert len(matches) == 1
    failure = matches[0]
    assert "그는 이 상황이 결코 정태의가 의도해서 벌어진 상황이 아니란 걸 이해해줄 것이다." in failure["source_text"]
    assert "鄭泰義也明白這種情況不可能是他故意製造的。" in failure["translation_text"]


def test_subject_shift_semantic_constraint_is_human_bounded():
    failure = FAILURES[0]
    assert failure["failure_category"] == "subject_reference_shift"
    assert failure["failure_subcategory"] is None
    assert failure["expected_semantic_constraint"] == "理解此情況的主體必須保持為前述遠方的男人；不得改為鄭泰義。"
    assert "認知主體錯置" in failure["observed_error"]


def test_no_root_cause_or_corrected_translation_is_invented():
    failure = FAILURES[0]
    assert failure["root_cause_status"] == "not_analyzed"
    assert failure["root_cause"] is None
    assert failure["corrected_translation_status"] == "not_provided"
    assert failure["corrected_translation"] is None


def test_failure_case_id_and_integrity_are_deterministic():
    failure = FAILURES[0]
    identity = {key: failure[key] for key in ("case_id", "alignment_id", "evidence_id", "failure_category", "source_sha256", "translation_sha256")}
    assert failure["failure_case_id"] == "TIC-FAIL-B4-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()
    body = dict(failure)
    integrity = body.pop("integrity")
    assert integrity["payload_sha256"] == sha256_bytes(canonical_json_bytes(body))


def test_failure_statistics_are_consistent():
    assert STATISTICS["total_failure_cases"] == 1
    assert STATISTICS["failure_category_counts"] == {"subject_reference_shift": 1}
    assert STATISTICS["severity_counts"] == {"unspecified": 1}
    assert STATISTICS["blocking_count"] == 0 and STATISTICS["nonblocking_count"] == 1
    assert STATISTICS["precisely_aligned_failure_count"] == 1
    assert STATISTICS["linked_but_not_aligned_count"] == 1
    assert STATISTICS["excluded_candidate_count"] == 3
    assert STATISTICS["root_cause_analyzed_count"] == 0
    assert STATISTICS["corrected_translation_available_count"] == 0


def test_failure_index_is_complete():
    assert len(INDEX["items"]) == 1
    required = {"failure_case_id", "case_id", "alignment_id", "evidence_id", "failure_category", "failure_subcategory", "severity", "blocking", "source_file", "translation_file", "provider", "model", "stage", "version", "review_source", "root_cause_status", "corrected_translation_status"}
    assert required <= set(INDEX["items"][0])
    assert INDEX["items"][0]["failure_case_id"] == FAILURES[0]["failure_case_id"]


def test_deterministic_rebuild_matches_canonical_artifacts():
    rebuilt = build_batch4_payloads(ROOT)
    for relative, payload in rebuilt.items():
        assert canonical_json_bytes(payload) == (ROOT / relative).read_bytes()


def test_duplicate_failure_evidence_is_rejected(monkeypatch):
    original_object = failure_module._object

    def duplicated(root, relative):
        value = original_object(root, relative)
        if relative == BATCH3_INPUTS[2]:
            value = copy.deepcopy(value)
            confirmed = next(item for item in value["alignment_units"] if item["quality_label"] == "human_confirmed_failure")
            value["alignment_units"].append(copy.deepcopy(confirmed))
        return value

    monkeypatch.setattr(failure_module, "_object", duplicated)
    with pytest.raises(ValueError, match="duplicate failure evidence"):
        build_batch4_payloads(ROOT)


def test_manifest_sha256_values_and_boundaries_are_valid():
    for relative in ("artifacts/tic_batch4/FAILURE_CORPUS_MANIFEST.json", "manifests/tic_batch4_human_confirmed_failure_corpus_manifest.json"):
        manifest = load(relative)
        assert all(file_sha(path) == digest for path, digest in manifest["files"].items())
    boundary = CORPUS["boundary"]
    assert boundary["failure_case_count"] == 1
    assert boundary["provider_executed"] is False and boundary["network_requests"] == 0
    assert boundary["new_translation_generated"] is False
    assert boundary["runtime_modified"] is False
    assert boundary["provider_modified"] is False
    assert boundary["prompt_modified"] is False
    assert boundary["stage11_modified"] is False
    assert boundary["stage12_modified"] is False
    assert boundary["golden_corpus_modified"] is False
    assert boundary["excellence_corpus_created"] is False
    assert boundary["tic_batch5_started"] is False


def test_historical_translation_sha256_values_are_unchanged_and_no_forbidden_imports_exist():
    cases = load("artifacts/tic_batch2/TRANSLATION_CASES.json")["translation_cases"]
    checked = set()
    for case in cases:
        if case["translation_file"] not in checked:
            assert file_sha(case["translation_file"]) == case["translation_sha256"]
            checked.add(case["translation_file"])
    for name in ("failure_corpus.py", "failure_index.py", "failure_statistics.py"):
        text = (ROOT / "core/translation_intelligence_corpus" / name).read_text(encoding="utf-8")
        imports = [line.lower() for line in text.splitlines() if line.startswith(("import ", "from "))]
        assert not any(word in line for line in imports for word in ("runtime", "provider", "prompt", "requests", "http"))
