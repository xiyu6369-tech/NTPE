from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.translation_intelligence_corpus.alignment import _apply_evidence, align_segments
from core.translation_intelligence_corpus.evidence_linker import link_all_evidence
from core.translation_intelligence_corpus.segmentation import reconstruct_text, segment_text

ROOT = Path(__file__).resolve().parents[2]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def file_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


CASES = load("artifacts/tic_batch2/TRANSLATION_CASES.json")["translation_cases"]
INVENTORY = load("artifacts/tic_batch3/MANUAL_EVIDENCE_INVENTORY.json")
LINKS = load("artifacts/tic_batch3/MANUAL_EVIDENCE_LINKS.json")
ALIGNMENTS = load("artifacts/tic_batch3/TRANSLATION_ALIGNMENT_UNITS.json")
STATISTICS = load("artifacts/tic_batch3/TRANSLATION_ALIGNMENT_STATISTICS.json")
INDEX = load("artifacts/tic_batch3/TRANSLATION_ALIGNMENT_INDEX.json")


def test_batch1_and_batch2_anchors_are_preserved():
    manifest = load("artifacts/tic_batch3/TRANSLATION_ALIGNMENT_MANIFEST.json")
    for path, digest in manifest["input_anchors"].items():
        assert file_sha(path) == digest
    assert len(CASES) == 125


def test_all_cases_are_traceable_and_ordered():
    unit_case_ids = {item["case_id"] for item in ALIGNMENTS["alignment_units"]}
    assert unit_case_ids == {case["case_id"] for case in CASES}
    assert [case["inventory_order"] for case in CASES] == sorted(case["inventory_order"] for case in CASES)


def test_evidence_provenance_is_fail_closed():
    types = {item["reviewer_type"] for item in INVENTORY["items"]}
    assert {"human", "automatic", "unknown"} <= types
    for item in INVENTORY["items"]:
        if item["reviewer_type"] != "human" or not item["human_provenance"]["complete"]:
            assert not item["usable_for_failure_corpus"]
            assert not item["usable_for_excellence_corpus"]


def test_evidence_links_are_deterministic_and_ambiguity_is_retained():
    fresh = link_all_evidence(INVENTORY["items"], CASES)
    for expected, stored in zip(fresh, LINKS["items"]):
        assert all(stored[key] == value for key, value in expected.items())
    unlinked = [item for item in LINKS["items"] if item["link_type"] == "unlinked"]
    assert unlinked and all(item["case_id"] is None for item in unlinked)


def test_source_and_translation_segmentation_preserve_text_offsets_and_sha():
    case = CASES[0]
    for language, key in (("ko", "source_text"), ("zh-Hant", "translation_text")):
        segments = segment_text(case[key], case_id=case["case_id"], language=language)
        assert reconstruct_text(segments) == case[key]
        for segment in segments:
            assert case[key][segment["start_offset"] : segment["end_offset"]] == segment["text"]
            assert hashlib.sha256(segment["text"].encode("utf-8")).hexdigest() == segment["text_sha256"]


def test_dialogue_and_narrative_segments_exist():
    segment_types = {item["segment_type"] for item in ALIGNMENTS["source_segments"] + ALIGNMENTS["translation_segments"]}
    assert "dialogue" in segment_types
    assert "narrative" in segment_types


def test_alignment_supports_non_one_to_one_types():
    types = {item["alignment_type"] for item in ALIGNMENTS["alignment_units"]}
    assert {"one_to_one", "one_to_many", "many_to_one", "many_to_many"} <= types


def test_unresolved_source_only_and_translation_only_fixtures_are_not_dropped():
    source = segment_text("A. B.", case_id="fixture", language="ko")
    translation = segment_text("甲。", case_id="fixture", language="zh-Hant")
    assert align_segments("fixture", source, translation)[0]["alignment_type"] == "many_to_one"
    assert align_segments("source-only", source, [])[0]["alignment_type"] == "source_only"
    assert align_segments("translation-only", [], translation)[0]["alignment_type"] == "translation_only"
    assert align_segments("unresolved", [], [])[0]["alignment_type"] == "unresolved"


def test_alignment_is_deterministic():
    case = CASES[1]
    source = segment_text(case["source_text"], case_id=case["case_id"], language="ko")
    translation = segment_text(case["translation_text"], case_id=case["case_id"], language="zh-Hant")
    assert align_segments(case["case_id"], source, translation) == align_segments(case["case_id"], source, translation)


def test_known_subject_shift_is_exactly_linked_and_human_confirmed():
    evidence_id = "TIC-EVID-B3-SUBJECT-SHIFT-001"
    link = next(item for item in LINKS["items"] if item["evidence_id"] == evidence_id)
    assert link["case_id"] == "TIC-CASE-B2-8AE44C56C7AD3DE4A6FD"
    assert link["human_confirmed"] is True
    units = [item for item in ALIGNMENTS["alignment_units"] if evidence_id in item["manual_evidence_ids"]]
    assert len(units) == 1
    unit = units[0]
    assert unit["quality_label"] == "human_confirmed_failure"
    assert unit["failure_category"] == "subject_reference_shift"
    assert unit["evidence_overlay"] is True
    assert unit["coverage_eligible"] is False
    assert unit["alignment_method"] == "manual_evidence_anchor"
    assert unit["alignment_confidence"] == "high"
    assert "그는 이 상황이 결코 정태의가 의도해서 벌어진 상황이 아니란 걸 이해해줄 것이다." in unit["source_text"]
    assert "鄭泰義也明白這種情況不可能是他故意製造的。" in unit["translation_text"]
    assert link["precise_alignment_status"] == "aligned"
    assert link["precise_alignment_unit_ids"] == [unit["alignment_id"]]


def test_case_level_match_does_not_propagate_failure():
    evidence_id = "TIC-EVID-B3-4C47ECCEDCAB1775DE59"
    link = next(item for item in LINKS["items"] if item["evidence_id"] == evidence_id)
    assert link["human_confirmed"] is True
    assert link["precise_alignment_status"] == "linked_but_not_aligned"
    assert link["precise_alignment_unit_ids"] == []
    assert not any(evidence_id in item["manual_evidence_ids"] for item in ALIGNMENTS["alignment_units"])


def _apply_fixture(source_text: str, translation_text: str, source_excerpt: str, translation_excerpt: str):
    case_id = "fixture-evidence"
    source = segment_text(source_text, case_id=case_id, language="ko") if source_text else []
    translation = segment_text(translation_text, case_id=case_id, language="zh-Hant") if translation_text else []
    units = align_segments(case_id, source, translation)
    evidence = {
        "evidence_id": "fixture-evidence-id",
        "quality_judgement": "human_confirmed_failure",
        "defect_categories": ["fixture_failure"],
        "excerpts": {"source": source_excerpt, "translation": translation_excerpt},
    }
    link = {
        "evidence_id": evidence["evidence_id"], "case_id": case_id,
        "human_confirmed": True, "link_confidence": "exact",
        "case_source_offset": source_text.find(source_excerpt) if source_excerpt in source_text else None,
        "case_translation_offset": translation_text.find(translation_excerpt) if translation_excerpt in translation_text else None,
    }
    _apply_evidence(units, {"items": [evidence]}, [link], source, translation)
    return units, link


def test_source_only_and_translation_only_units_never_receive_translation_failure():
    source_units, source_link = _apply_fixture("원문.", "", "원문.", "譯文。")
    translation_units, translation_link = _apply_fixture("", "譯文。", "원문.", "譯文。")
    assert all(item["quality_label"] != "human_confirmed_failure" for item in source_units + translation_units)
    assert all(item["alignment_type"] in {"source_only", "translation_only"} for item in source_units + translation_units)
    assert source_link["precise_alignment_status"] == "linked_but_not_aligned"
    assert translation_link["precise_alignment_status"] == "linked_but_not_aligned"


def test_missing_source_or_translation_coverage_never_marks_failure():
    source_missing, source_link = _apply_fixture("다른 원문.", "問題譯文。", "필요 원문.", "問題譯文。")
    translation_missing, translation_link = _apply_fixture("필요 원문.", "다른譯文。", "필요 원문.", "問題譯文。")
    assert all(item["quality_label"] != "human_confirmed_failure" for item in source_missing + translation_missing)
    assert source_link["precise_alignment_status"] == "linked_but_not_aligned"
    assert translation_link["precise_alignment_status"] == "linked_but_not_aligned"


def test_no_revision_or_automatic_excellence_was_created():
    review = load("artifacts/tic_batch3/KNOWN_SUBJECT_SHIFT_HUMAN_REVIEW.json")
    assert review["approved_revision"] is None
    assert review["new_translation_generated"] is False
    assert STATISTICS["human_confirmed_excellence_units"] == 0


def test_statistics_and_coverage_include_unmatched_units():
    units = ALIGNMENTS["alignment_units"]
    coverage_units = [item for item in units if item["coverage_eligible"]]
    assert STATISTICS["total_alignment_units"] == len(units)
    assert STATISTICS["total_source_segments"] == len(ALIGNMENTS["source_segments"])
    assert STATISTICS["total_translation_segments"] == len(ALIGNMENTS["translation_segments"])
    covered = sum(item["alignment_type"] not in {"source_only", "translation_only", "unresolved"} for item in coverage_units)
    assert STATISTICS["alignment_coverage"] == covered / len(coverage_units)
    assert STATISTICS["coverage_eligible_alignment_units"] == len(coverage_units)
    assert STATISTICS["evidence_overlay_count"] == 1
    assert STATISTICS["human_confirmed_failure_evidence_count"] == 2
    assert STATISTICS["human_confirmed_failure_unit_count"] == 1
    assert STATISTICS["evidence_without_precise_alignment_count"] == 1


def test_all_historical_translation_sha256_values_are_unchanged():
    checked = set()
    for case in CASES:
        path = case["translation_file"]
        if path not in checked:
            assert file_sha(path) == case["translation_sha256"]
            checked.add(path)


def test_index_is_complete_and_searchable():
    assert len(INDEX["items"]) == len(ALIGNMENTS["alignment_units"])
    required = {"alignment_id", "case_id", "corpus_id", "source_file", "translation_file", "stage", "version", "provider", "model", "segment_type", "alignment_type", "alignment_confidence", "review_status", "quality_label", "failure_category", "manual_evidence_id"}
    assert all(required <= set(item) for item in INDEX["items"])


def test_manifests_have_valid_sha256_and_frozen_boundaries():
    for manifest_path in ("artifacts/tic_batch3/TRANSLATION_ALIGNMENT_MANIFEST.json", "manifests/tic_batch3_manual_evidence_alignment_manifest.json"):
        manifest = load(manifest_path)
        for path, digest in manifest["files"].items():
            assert file_sha(path) == digest
    boundaries = load("manifests/tic_batch3_manual_evidence_alignment_manifest.json")["boundaries"]
    assert boundaries["provider_executed"] is False
    assert boundaries["network_requests"] == 0
    assert boundaries["new_translation_generated"] is False
    assert boundaries["tic_batch4_started"] is False


def test_batch3_modules_do_not_import_runtime_or_provider():
    for name in ("segmentation.py", "evidence_linker.py", "alignment.py"):
        text = (ROOT / "core/translation_intelligence_corpus" / name).read_text(encoding="utf-8")
        imports = [line.lower() for line in text.splitlines() if line.startswith(("import ", "from "))]
        assert not any("runtime" in line or "provider" in line for line in imports)
