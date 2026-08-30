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
EXECUTION = STAGE / "TE_V72_STAGE1222_INDEPENDENT_PAIR_EXECUTION.json"
REVIEW = STAGE / "TE_V72_STAGE1222_MANUAL_AB_REVIEW.json"
SOURCE_SHA = "ac76cf63de96d465d23ed6a131fbc1008ed06adae76c8e0668b27e58cde1c2b5"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _canonical_sha(payload: dict) -> str:
    return _sha_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _meta(arm: str) -> dict:
    return _load(STAGE / arm / "execution_metadata.json")


def _request(arm: str) -> dict:
    return _load(STAGE / arm / "request.json")


def _prompts():
    source = split_text((ROOT / "tests/literary/Golden_Set/original_ko.txt").read_text(encoding="utf-8"), 600)[0]
    common = dict(chunk_text=source, locked_dictionary={}, alias_map={}, previous_context="", profile="literary")
    return source, build_literary_prompt(**common, candidate_enabled=False), build_literary_prompt(**common, candidate_enabled=True)


def test_historical_stage1221_manifest_is_unchanged() -> None:
    execution = _load(EXECUTION)
    path = "manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json"
    assert execution["anchors"][path] == _sha_bytes((ROOT / path).read_bytes())


def test_historical_stage1221_inventory_is_unchanged() -> None:
    manifest = _load(ROOT / "manifests/te_v720_stage1221_controlled_provider_ab_execution_manifest.json")
    for name, digest in manifest["files"].items():
        assert _sha_bytes((ROOT / name).read_bytes()) == digest


def test_execution_order_is_independent_baseline_then_candidate() -> None:
    execution = _load(EXECUTION)
    assert execution["independent_arms"] is True
    assert execution["execution_order"] == ["baseline", "candidate"]


def test_each_arm_executed_exactly_once() -> None:
    execution = _load(EXECUTION)
    assert execution["baseline_requests"] == 1 and execution["candidate_requests"] == 1
    assert _meta("baseline")["session_summary"]["attempts_executed"] == 1
    assert _meta("candidate")["session_summary"]["attempts_executed"] == 1


def test_total_requests_do_not_exceed_two() -> None:
    assert _load(EXECUTION)["network_requests"] == 2


def test_baseline_failure_did_not_block_candidate() -> None:
    assert _meta("baseline")["success"] is False
    assert _meta("candidate")["network_requests"] == 1


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_no_retry_or_fallback(arm: str) -> None:
    meta = _meta(arm)
    assert meta["retry_count"] == 0 and meta["attempt_limit"] == 1
    assert meta["fallback_used"] is False


@pytest.mark.parametrize("field,expected", [
    ("source_sha256", SOURCE_SHA),
    ("model", "meta/llama-3.2-90b-vision-instruct"),
    ("timeout_seconds", 180),
    ("max_output_tokens", 800),
    ("chunk_size", 600),
    ("provider", "nvidia"),
    ("temperature", 0.12),
    ("top_p", 0.82),
])
def test_fixed_settings_match_between_arms(field: str, expected: object) -> None:
    assert _meta("baseline")[field] == expected
    assert _meta("candidate")[field] == expected


@pytest.mark.parametrize("field", ["system_sha256", "context_sha256", "glossary_sha256", "source_section_sha256"])
def test_fixed_prompt_components_match(field: str) -> None:
    assert _meta("baseline")[field] == _meta("candidate")[field]


def test_only_configuration_switch_is_candidate_enabled() -> None:
    assert _request("baseline")["candidate_enabled"] is False
    assert _request("candidate")["candidate_enabled"] is True


def test_only_prompt_difference_is_stage121_candidate_policy() -> None:
    _, baseline, candidate = _prompts()
    assert candidate.user_prompt.replace("\n" + CANDIDATE_POLICY, "", 1) == baseline.user_prompt
    assert _meta("baseline")["prompt_sha256"] == _sha_text(baseline.user_prompt)
    assert _meta("candidate")["prompt_sha256"] == _sha_text(candidate.user_prompt)


def test_source_is_exact_frozen_unit() -> None:
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


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_each_arm_timed_out_once(arm: str) -> None:
    meta = _meta(arm)
    assert meta["success"] is False and meta["status"] == "failed"
    assert meta["exception_category"] == "timeout" and meta["http_status"] is None
    assert 180 <= meta["elapsed_seconds"] < 181


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_failed_translation_is_empty_and_unfabricated(arm: str) -> None:
    path = STAGE / arm / "translation.txt"
    assert path.is_file() and path.read_text(encoding="utf-8") == ""
    assert _meta(arm)["translation_sha256"] is None


def test_pair_status_is_failed_when_both_translations_empty() -> None:
    execution = _load(EXECUTION)
    assert execution["status"] == "ab_pair_failed"
    assert execution["baseline_success"] is False and execution["candidate_success"] is False


def test_complete_status_requires_two_nonempty_translations() -> None:
    execution = _load(EXECUTION)
    nonempty = all((STAGE / arm / "translation.txt").read_text(encoding="utf-8").strip() for arm in ("baseline", "candidate"))
    assert (execution["status"] == "ab_pair_complete") is bool(nonempty)


def test_failed_pair_is_not_reviewable() -> None:
    execution, review = _load(EXECUTION), _load(REVIEW)
    assert execution["review_status"] == "not_reviewable_pair_incomplete"
    assert review["status"] == "not_reviewable_pair_incomplete"


@pytest.mark.parametrize("field", [
    "unsupported_additions", "omissions", "meaning_distortion", "naturalness",
    "narrative_flow", "dialogue", "character_voice", "historical_contextual_tone",
    "terminology", "traditional_chinese_consistency", "blocking_defects",
    "overall_judgement", "review_reason",
])
def test_review_fields_remain_null(field: str) -> None:
    assert _load(REVIEW)["review"][field] is None


def test_review_is_manual_only() -> None:
    review = _load(REVIEW)
    assert review["manual_review_completed"] is False
    assert review["automated_scoring_performed"] is False
    assert review["allowed_overall_judgements"] == [
        "baseline_better", "candidate_better", "equivalent",
        "both_unacceptable", "insufficient_evidence",
    ]


@pytest.mark.parametrize("arm", ["baseline", "candidate"])
def test_sanitized_response_has_no_headers_or_credentials(arm: str) -> None:
    response = _load(STAGE / arm / "raw_response.json")
    assert response["sensitive_headers_removed"] is True
    assert response["headers_persisted"] is False
    assert response["api_key_persisted"] is False
    assert response["authorization_header_persisted"] is False


def test_stage_artifacts_do_not_contain_secret() -> None:
    content = b"\n".join(path.read_bytes() for path in STAGE.rglob("*") if path.is_file())
    assert b"Bearer " not in content and b"NVIDIA_API_KEY" not in content
    key = os.environ.get("NVIDIA_API_KEY", "").encode("utf-8")
    assert not key or key not in content


@pytest.mark.parametrize("field", [
    "prompt_modified", "candidate_modified", "runtime_modified", "provider_modified",
    "model_modified", "timeout_modified", "retry_modified", "chunking_modified",
    "comparison_executed", "manual_review_completed", "quality_improvement_verified",
    "quality_candidate_accepted", "stage123_started",
])
def test_forbidden_boundary_remains_false(field: str) -> None:
    assert _load(EXECUTION)["boundary"][field] is False


def test_stage123_not_started() -> None:
    assert not (ROOT / "artifacts/te_v72_stage123").exists()
    assert not any(ROOT.glob("*v720_stage123*"))
