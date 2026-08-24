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
EXECUTION = STAGE / "TE_V72_STAGE1221_CONTROLLED_AB_EXECUTION.json"
REVIEW = STAGE / "TE_V72_STAGE1221_MANUAL_AB_REVIEW.json"
SOURCE_SHA = "ac76cf63de96d465d23ed6a131fbc1008ed06adae76c8e0668b27e58cde1c2b5"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _canonical_sha(payload: dict) -> str:
    return _sha_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _metadata(arm: str) -> dict:
    return _load(STAGE / arm / "execution_metadata.json")


def _request(arm: str) -> dict:
    return _load(STAGE / arm / "request.json")


def _prompts():
    source = split_text((ROOT / "tests/literary/Golden_Set/original_ko.txt").read_text(encoding="utf-8"), 600)[0]
    common = dict(chunk_text=source, locked_dictionary={}, alias_map={}, previous_context="", profile="literary")
    return source, build_literary_prompt(**common, candidate_enabled=False), build_literary_prompt(**common, candidate_enabled=True)


def test_execution_status_records_incomplete_pair() -> None:
    payload = _load(EXECUTION)
    assert payload["status"] == "ab_pair_incomplete"
    assert payload["execution_order"] == ["baseline"]


def test_request_count_never_exceeds_two() -> None:
    payload = _load(EXECUTION)
    assert payload["network_requests"] == 1 <= 2
    assert payload["baseline_requests"] == 1 and payload["candidate_requests"] == 0


def test_baseline_executed_at_most_once() -> None:
    meta = _metadata("baseline")
    assert meta["request_number"] == 1 and meta["network_requests"] == 1
    assert meta["session_summary"]["attempts_executed"] == 1


def test_candidate_was_not_called_after_baseline_failure() -> None:
    meta = _metadata("candidate")
    assert meta["request_number"] == 2 and meta["network_requests"] == 0
    assert meta["status"] == "not_executed_baseline_failed"


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_retry_and_fallback_are_zero(arm: str) -> None:
    meta = _metadata(arm)
    assert meta["retry_count"] == 0 and meta["attempt_limit"] == 1
    assert meta["fallback_used"] is False


@pytest.mark.parametrize("field,expected", [
    ("source_sha256", SOURCE_SHA),
    ("model", "meta/llama-3.3-70b-instruct"),
    ("timeout_seconds", 180),
    ("max_output_tokens", 800),
    ("chunk_size", 600),
    ("provider", "nvidia"),
    ("temperature", 0.12),
    ("top_p", 0.82),
])
def test_ab_execution_settings_are_identical(field: str, expected: object) -> None:
    assert _metadata("baseline")[field] == expected
    assert _metadata("candidate")[field] == expected


@pytest.mark.parametrize("field", [
    "system_sha256", "context_sha256", "glossary_sha256", "source_section_sha256",
])
def test_non_candidate_prompt_components_match(field: str) -> None:
    assert _metadata("baseline")[field] == _metadata("candidate")[field]


def test_candidate_flag_is_only_configuration_switch() -> None:
    assert _request("baseline")["candidate_enabled"] is False
    assert _request("candidate")["candidate_enabled"] is True


def test_only_prompt_delta_is_frozen_candidate_policy() -> None:
    _, baseline, candidate = _prompts()
    assert candidate.user_prompt.replace("\n" + CANDIDATE_POLICY, "", 1) == baseline.user_prompt
    assert _metadata("baseline")["prompt_sha256"] == _sha_text(baseline.user_prompt)
    assert _metadata("candidate")["prompt_sha256"] == _sha_text(candidate.user_prompt)


def test_source_unit_is_exact_stage10101_chunk() -> None:
    source, _, _ = _prompts()
    assert len(source) == 575 and _sha_text(source) == SOURCE_SHA


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_request_sha_is_valid(arm: str) -> None:
    request = _request(arm)
    keys = [
        "candidate_enabled", "request_number", "provider", "model", "timeout_seconds",
        "attempt_limit", "retry_count", "max_output_tokens", "chunk_size", "source_sha256",
        "system_sha256", "policy_sha256", "context_sha256", "glossary_sha256",
        "source_section_sha256", "prompt_sha256", "temperature", "top_p", "fallback_used",
    ]
    assert request["request_sha256"] == _canonical_sha({key: request[key] for key in keys})


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_response_sha_is_valid(arm: str) -> None:
    response = _load(STAGE / arm / "raw_response.json")
    expected = response.pop("response_sha256")
    assert expected == _canonical_sha(response)


def test_baseline_timeout_is_preserved_without_translation() -> None:
    meta = _metadata("baseline")
    assert meta["success"] is False and meta["status"] == "failed"
    assert meta["exception_category"] == "timeout" and meta["http_status"] is None
    assert 180 <= meta["elapsed_seconds"] < 181
    assert meta["translation_sha256"] is None


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_translation_file_is_not_fabricated(arm: str) -> None:
    path = STAGE / arm / "translation.txt"
    assert path.is_file() and path.read_text(encoding="utf-8") == ""
    assert _metadata(arm)["translation_sha256"] is None


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_raw_response_contains_no_headers_or_credentials(arm: str) -> None:
    response = _load(STAGE / arm / "raw_response.json")
    assert response["sensitive_headers_removed"] is True
    assert response["headers_persisted"] is False
    assert response["api_key_persisted"] is False
    assert response["authorization_header_persisted"] is False


def test_artifact_tree_does_not_contain_api_key_or_bearer_header() -> None:
    combined = b"\n".join(path.read_bytes() for path in STAGE.rglob("*") if path.is_file())
    assert b"Bearer " not in combined and b"NVIDIA_API_KEY" not in combined
    key = os.environ.get("NVIDIA_API_KEY", "").encode("utf-8")
    assert not key or key not in combined


def test_stage121_and_stage122_anchors_are_unchanged() -> None:
    execution = _load(EXECUTION)
    assert execution["anchors"]["stage121_manifest_sha256"] == _sha_bytes((ROOT / "manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json").read_bytes())
    assert execution["anchors"]["stage122_manifest_sha256"] == _sha_bytes((ROOT / "manifests/te_v720_stage122_controlled_provider_ab_validation_manifest.json").read_bytes())


def test_original_stage122_manifest_inventory_is_unchanged() -> None:
    manifest = _load(ROOT / "manifests/te_v720_stage122_controlled_provider_ab_validation_manifest.json")
    for name, digest in manifest["files"].items():
        assert _sha_bytes((ROOT / name).read_bytes()) == digest


@pytest.mark.parametrize("field", [
    "unsupported_additions", "omissions", "meaning_distortion", "naturalness",
    "narrative_flow", "dialogue", "character_voice", "historical_contextual_tone",
    "terminology", "traditional_chinese_consistency", "blocking_defects",
    "overall_judgement", "review_reason",
])
def test_manual_review_field_remains_null(field: str) -> None:
    assert _load(REVIEW)["review"][field] is None


def test_manual_review_allowed_results_are_exact() -> None:
    review = _load(REVIEW)
    assert review["allowed_overall_judgements"] == [
        "baseline_better", "candidate_better", "equivalent",
        "both_unacceptable", "insufficient_evidence",
    ]
    assert review["manual_review_completed"] is False
    assert review["automated_scoring_performed"] is False


def test_execution_boundary_is_truthful() -> None:
    boundary = _load(EXECUTION)["boundary"]
    assert boundary["real_provider_executed"] is True
    assert boundary["new_translation_generated"] is False
    assert boundary["comparison_executed"] is False
    assert boundary["quality_improvement_verified"] is False
    assert boundary["quality_candidate_accepted"] is False


@pytest.mark.parametrize("field", [
    "prompt_modified", "candidate_modified", "runtime_modified", "provider_modified",
    "model_modified", "timeout_modified", "retry_modified", "stage123_started",
])
def test_forbidden_boundary_remains_false(field: str) -> None:
    assert _load(EXECUTION)["boundary"][field] is False


def test_no_stage123_artifacts_started() -> None:
    assert not (ROOT / "artifacts/te_v72_stage123").exists()
    assert not any(ROOT.glob("*v720_stage123*"))
