from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from core.literary_prompt_quality_candidate_v72 import CANDIDATE_POLICY, build_literary_prompt
from lts.txt_translation_runtime import split_text

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v72_canary"
STAGE = FIXTURES
FREEZE = STAGE / "TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json"
EXECUTION = STAGE / "TE_V72_STAGE1223_MINIMAL_EXCERPT_AB_EXECUTION.json"
REVIEW = STAGE / "TE_V72_STAGE1223_MANUAL_AB_REVIEW.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _canonical_sha(payload: dict) -> str:
    return _sha_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _excerpt() -> str:
    freeze = _load(FREEZE)
    source = Path(freeze["parent_source_reference"])
    if not source.is_absolute():
        source = ROOT / source
    unit = split_text(source.read_text(encoding="utf-8"), 600)[0]
    return unit[freeze["excerpt_start_offset"]:freeze["excerpt_end_offset"]]


def _meta(arm: str) -> dict:
    return _load(STAGE / arm / "execution_metadata.json")


def _request(arm: str) -> dict:
    return _load(STAGE / arm / "request.json")


def _prompts():
    excerpt = _excerpt()
    common = dict(chunk_text=excerpt, locked_dictionary={}, alias_map={}, previous_context="", profile="literary")
    return build_literary_prompt(**common, candidate_enabled=False), build_literary_prompt(**common, candidate_enabled=True)


def test_parent_source_path_and_hash_are_correct() -> None:
    freeze = _load(FREEZE)
    path = ROOT / freeze["parent_source_reference"]
    assert path == ROOT / "tests/literary/Golden_Set/original_ko.txt"
    assert _sha_bytes(path.read_bytes()) == freeze["parent_source_sha256"]


def test_parent_source_unit_is_exact_stage10101_chunk() -> None:
    freeze = _load(FREEZE)
    unit = split_text((ROOT / freeze["parent_source_reference"]).read_text(encoding="utf-8"), 600)[0]
    assert _sha_text(unit) == freeze["parent_source_unit_sha256"]
    assert freeze["parent_source_unit"] == "Golden_Set:1"


def test_offsets_deterministically_reconstruct_excerpt() -> None:
    freeze, excerpt = _load(FREEZE), _excerpt()
    assert len(excerpt) == freeze["excerpt_length"]
    assert _sha_text(excerpt) == freeze["excerpt_sha256"]


def test_excerpt_length_is_within_required_bounds() -> None:
    assert 120 <= len(_excerpt()) <= 220
    assert len(_excerpt()) == 153


def test_excerpt_is_frozen_and_not_persisted_in_freeze_artifact() -> None:
    freeze = _load(FREEZE)
    assert freeze["excerpt_frozen"] is True and freeze["excerpt_text_persisted"] is False
    assert _excerpt() not in FREEZE.read_text(encoding="utf-8")


def test_selection_reason_is_evidence_based() -> None:
    freeze = _load(FREEZE)
    assert len(freeze["evidence_references"]) >= 3
    assert "TQ-DEF-A" in freeze["evidence_references"][0]
    assert set(freeze["covered_quality_risks"]) >= {"literal or unnatural phrasing", "narrative naturalness"}


@pytest.mark.parametrize("path", [
    "manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json",
    "manifests/te_v720_stage122_controlled_provider_ab_validation_manifest.json",
    "manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json",
    "manifests/te_v720_stage1222_independent_pair_recovery_execution_manifest.json",
])
def test_historical_manifest_anchor_is_unchanged(path: str) -> None:
    assert _load(EXECUTION)["anchors"][path] == _sha_bytes((ROOT / path).read_bytes())


def test_stage1221_and_stage1222_historical_inventories_are_unchanged() -> None:
    for manifest_name in (
        "manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json",
        "manifests/te_v720_stage1222_independent_pair_recovery_execution_manifest.json",
    ):
        manifest = _load(ROOT / manifest_name)
        for path, digest in manifest["files"].items():
            assert _sha_bytes((ROOT / path).read_bytes()) == digest


def test_both_arms_use_same_excerpt() -> None:
    assert _request("baseline")["source_excerpt_sha256"] == _request("candidate")["source_excerpt_sha256"] == _load(FREEZE)["excerpt_sha256"]
    assert _request("baseline")["excerpt_start_offset"] == _request("candidate")["excerpt_start_offset"] == 0
    assert _request("baseline")["excerpt_end_offset"] == _request("candidate")["excerpt_end_offset"] == 153


def test_only_prompt_difference_is_candidate_policy() -> None:
    baseline, candidate = _prompts()
    assert candidate.user_prompt.replace("\n" + CANDIDATE_POLICY, "", 1) == baseline.user_prompt
    assert _meta("baseline")["prompt_sha256"] == _sha_text(baseline.user_prompt)
    assert _meta("candidate")["prompt_sha256"] == _sha_text(candidate.user_prompt)


@pytest.mark.parametrize("field", ["system_sha256", "context_sha256", "glossary_sha256", "source_section_sha256"])
def test_fixed_prompt_components_are_identical(field: str) -> None:
    assert _meta("baseline")[field] == _meta("candidate")[field]


@pytest.mark.parametrize("field,expected", [
    ("model", "meta/llama-3.2-90b-vision-instruct"),
    ("timeout_seconds", 180),
    ("max_output_tokens", 800),
    ("chunk_size", 600),
    ("provider", "nvidia"),
    ("temperature", 0.12),
    ("top_p", 0.82),
])
def test_fixed_execution_setting_is_identical(field: str, expected: object) -> None:
    assert _meta("baseline")[field] == expected
    assert _meta("candidate")[field] == expected


def test_each_arm_executed_once_and_total_is_two() -> None:
    execution = _load(EXECUTION)
    assert execution["baseline_requests"] == 1 and execution["candidate_requests"] == 1
    assert execution["network_requests"] == 2
    assert _meta("baseline")["session_summary"]["attempts_executed"] == 1
    assert _meta("candidate")["session_summary"]["attempts_executed"] == 1


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_no_retry_fallback_or_postprocessing(arm: str) -> None:
    meta = _meta(arm)
    assert meta["retry_count"] == 0 and meta["attempt_limit"] == 1
    assert meta["fallback_used"] is False and meta["translation_postprocessed"] is False


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_request_sha_is_valid(arm: str) -> None:
    request = _request(arm)
    keys = [
        "candidate_enabled", "request_number", "provider", "model", "timeout_seconds",
        "attempt_limit", "retry_count", "max_output_tokens", "chunk_size",
        "parent_source_unit_sha256", "source_excerpt_sha256", "excerpt_start_offset",
        "excerpt_end_offset", "system_sha256", "policy_sha256", "context_sha256",
        "glossary_sha256", "source_section_sha256", "prompt_sha256", "temperature",
        "top_p", "fallback_used",
    ]
    assert request["request_sha256"] == _canonical_sha({key: request[key] for key in keys})


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_response_sha_is_valid(arm: str) -> None:
    response = _load(STAGE / arm / "raw_response.json")
    expected = response.pop("response_sha256")
    assert expected == _canonical_sha(response)


def test_baseline_translation_is_exact_provider_output() -> None:
    translation = (STAGE / "baseline/translation.txt").read_text(encoding="utf-8")
    response = _load(STAGE / "baseline/raw_response.json")
    assert translation and translation == response["content"]
    assert _meta("baseline")["translation_sha256"] == _sha_text(translation)
    assert _meta("baseline")["success"] is True


def test_candidate_timeout_has_empty_translation() -> None:
    assert (STAGE / "candidate/translation.txt").read_text(encoding="utf-8") == ""
    assert _meta("candidate")["success"] is False
    assert _meta("candidate")["exception_category"] == "timeout"
    assert _meta("candidate")["translation_sha256"] is None


def test_partial_status_matches_one_successful_arm() -> None:
    execution = _load(EXECUTION)
    assert execution["status"] == "ab_pair_partial"
    assert execution["baseline_success"] is True and execution["candidate_success"] is False


def test_only_complete_pair_can_be_reviewed() -> None:
    execution, review = _load(EXECUTION), _load(REVIEW)
    assert execution["status"] != "ab_pair_complete"
    assert execution["review_status"] == review["status"] == "not_reviewable_pair_incomplete"


@pytest.mark.parametrize("field", [
    "unsupported_additions", "omissions", "meaning_distortion", "naturalness",
    "narrative_flow", "dialogue", "character_voice", "historical_contextual_tone",
    "terminology", "traditional_chinese_consistency", "blocking_defects",
    "overall_judgement", "review_reason",
])
def test_manual_review_fields_remain_null(field: str) -> None:
    assert _load(REVIEW)["review"][field] is None


def test_review_is_not_automatically_scored() -> None:
    review = _load(REVIEW)
    assert review["manual_review_completed"] is False and review["automated_scoring_performed"] is False
    assert review["allowed_overall_judgements"] == [
        "baseline_better", "candidate_better", "equivalent",
        "both_unacceptable", "insufficient_evidence",
    ]


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_sanitized_response_has_no_secret_headers(arm: str) -> None:
    response = _load(STAGE / arm / "raw_response.json")
    assert response["sensitive_headers_removed"] is True
    assert response["headers_persisted"] is False
    assert response["api_key_persisted"] is False
    assert response["authorization_header_persisted"] is False


def test_artifacts_do_not_persist_key_or_full_parent_source() -> None:
    combined = b"\n".join(path.read_bytes() for path in STAGE.rglob("*") if path.is_file())
    assert b"Bearer " not in combined and b"NVIDIA_API_KEY" not in combined
    key = os.environ.get("NVIDIA_API_KEY", "").encode("utf-8")
    assert not key or key not in combined
    parent = split_text((ROOT / "tests/literary/Golden_Set/original_ko.txt").read_text(encoding="utf-8"), 600)[0].encode("utf-8")
    assert parent not in combined


@pytest.mark.parametrize("field", [
    "parent_source_modified", "prompt_modified", "candidate_modified", "runtime_modified",
    "provider_modified", "model_modified", "timeout_modified", "retry_modified",
    "comparison_executed", "manual_review_completed", "quality_improvement_verified",
    "quality_candidate_accepted", "stage123_started",
])
def test_forbidden_boundary_remains_false(field: str) -> None:
    assert _load(EXECUTION)["boundary"][field] is False


def test_stage123_not_started() -> None:
    assert not (ROOT / "artifacts/te_v72_stage123").exists()
    assert not any(ROOT.glob("*v720_stage123*"))
