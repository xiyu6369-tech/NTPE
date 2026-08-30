from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from core.translation_quality_canary import (
    BASELINE_FLAGS,
    CANDIDATE_FLAGS,
    CHECKLIST,
    CanaryConfiguration,
    build_comparison_report,
    run_offline_canary_case,
)


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _configuration() -> CanaryConfiguration:
    return CanaryConfiguration(
        model="meta/llama-3.2-90b-vision-instruct",
        timeout_seconds=180,
        glossary_sha256="a" * 64,
        profile="literary-ko-zh-TW",
        corpus_sha256=hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
    )


def _pair():
    return run_offline_canary_case(
        case_id="canary-unit",
        categories=("character_name", "context_continuity"),
        source_text="영희가 조용히 말했다.",
        configuration=_configuration(),
    )


def test_baseline_and_candidate_flags_are_exact() -> None:
    assert BASELINE_FLAGS.to_dict() == {
        "integration": False, "character_memory": False,
        "context_scene": False, "naturalness": False, "kill_switch": False,
    }
    assert CANDIDATE_FLAGS.to_dict() == {
        "integration": True, "character_memory": True,
        "context_scene": True, "naturalness": True, "kill_switch": False,
    }


def test_pair_uses_identical_configuration_and_only_flags_differ() -> None:
    pair = _pair()
    assert pair.parity_verified is True
    assert pair.only_feature_flags_differ is True
    assert pair.baseline.source_sha256 == pair.candidate.source_sha256
    assert pair.baseline.input_fingerprint == pair.candidate.input_fingerprint
    assert pair.baseline.configuration_fingerprint == pair.candidate.configuration_fingerprint


def test_disabled_path_is_exact_baseline_and_candidate_exercises_all_inputs() -> None:
    pair = _pair()
    expected = _sha("CONTROLLED CANARY BASELINE\n영희가 조용히 말했다.")
    assert pair.baseline.prompt_sha256 == expected
    assert pair.baseline.budget_usage_tokens == 0
    assert pair.candidate.prompt_sha256 != expected
    assert pair.candidate.character_selected >= 1
    assert pair.candidate.context_selected >= 1
    assert pair.candidate.scene_selected >= 1
    assert pair.candidate.budget_usage_tokens > 0


def test_offline_runner_adds_no_provider_or_network_requests() -> None:
    pair = _pair()
    for arm in (pair.baseline, pair.candidate):
        assert arm.provider_requests == arm.network_requests == 0
        assert arm.translation_executed is False
        assert arm.translation_sha256 is None


def test_semantic_outputs_are_deterministic_across_three_runs() -> None:
    pairs = [_pair() for _ in range(3)]
    for field in ("source_sha256", "input_fingerprint", "configuration_fingerprint", "prompt_sha256"):
        assert len({getattr(pair.candidate, field) for pair in pairs}) == 1
    assert len({pair.candidate.budget_usage_tokens for pair in pairs}) == 1


def test_unreviewed_comparison_fails_closed_without_false_quality_claim() -> None:
    report = build_comparison_report([_pair()], corpus_human_reviewed=False)
    assert report["canary_pass"] is False
    assert report["status"] == "FAIL_CLOSED_INSUFFICIENT_QUALITY_EVIDENCE"
    assert report["reviewed_checklist_rows"] == 0
    assert report["expected_checklist_rows"] == len(CHECKLIST)
    assert all(
        row["result"] == "Same" and row["evidence_status"] == "insufficient_evidence"
        for row in report["chunks"][0]["checklist"]
    )


def test_complete_human_reviewed_nonregressing_pair_can_pass() -> None:
    pair = _pair()
    baseline = replace(pair.baseline, translation_executed=True, translation_sha256="b" * 64)
    candidate = replace(pair.candidate, translation_executed=True, translation_sha256="c" * 64)
    complete = replace(pair, baseline=baseline, candidate=candidate)
    reviews = {complete.case_id: {dimension: "Same" for dimension in CHECKLIST}}
    report = build_comparison_report([complete], reviews, corpus_human_reviewed=True)
    assert report["canary_pass"] is True
    assert report["status"] == "PASS"


def test_required_quality_regression_blocks_pass() -> None:
    pair = _pair()
    complete = replace(
        pair,
        baseline=replace(pair.baseline, translation_executed=True, translation_sha256="b" * 64),
        candidate=replace(pair.candidate, translation_executed=True, translation_sha256="c" * 64),
    )
    reviews = {complete.case_id: {dimension: "Same" for dimension in CHECKLIST}}
    reviews[complete.case_id]["naturalness"] = "Regressed"
    assert build_comparison_report([complete], reviews, corpus_human_reviewed=True)["canary_pass"] is False


def test_invalid_review_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid comparison value"):
        build_comparison_report([_pair()], {"canary-unit": {"naturalness": "PASS"}}, corpus_human_reviewed=True)


def test_engineering_corpus_has_six_non_easy_chunks_and_required_coverage() -> None:
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert len(payload["cases"]) == 6
    assert payload["human_reviewed_translation_pairs"] is False
    coverage = {category for case in payload["cases"] for category in case["categories"]}
    required = {
        "character_name", "multiple_characters", "honorific", "scene_transition",
        "long_sentence", "korean_omitted_subject", "pronoun_resolution", "long_dialogue",
        "narrative_dialogue_mix", "era_background",
    }
    assert coverage >= required


def test_empty_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        run_offline_canary_case(
            case_id="empty", categories=(), source_text=" ", configuration=_configuration()
        )
