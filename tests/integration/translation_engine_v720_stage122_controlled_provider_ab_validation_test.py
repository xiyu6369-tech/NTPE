from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.literary_prompt_quality_candidate_v72 import CANDIDATE_POLICY, build_literary_prompt
from lts.txt_translation_runtime import split_text

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "artifacts/te_v72_stage122"
PACKAGE = STAGE / "TE_V72_STAGE122_AB_EXECUTION_PACKAGE.json"
REVIEW = STAGE / "TE_V72_STAGE122_MANUAL_AB_REVIEW.json"
SOURCE = ROOT / "tests/literary/Golden_Set/original_ko.txt"


def _load(name: str) -> dict:
    return json.loads((STAGE / name).read_text(encoding="utf-8"))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prompts():
    source = split_text(SOURCE.read_text(encoding="utf-8"), 600)[0]
    kwargs = dict(chunk_text=source, locked_dictionary={}, alias_map={}, previous_context="", profile="literary")
    return source, build_literary_prompt(**kwargs, candidate_enabled=False), build_literary_prompt(**kwargs, candidate_enabled=True)


def test_stage11_freeze_anchor_is_unchanged() -> None:
    assert _sha_file(ROOT / "manifests/te_v710_stage118_translation_quality_framework_freeze_manifest.json") == "b5eed41b1c17ebea77db7b021db9fd021d746a0822ce5071ade4dcfc3acbafcf"


def test_stage121_candidate_is_unchanged() -> None:
    manifest = json.loads((ROOT / "manifests/te_v720_stage121_evidence_based_prompt_quality_candidate_manifest.json").read_text(encoding="utf-8"))
    path = "core/literary_prompt_quality_candidate_v72/candidate.py"
    assert _sha_file(ROOT / path) == manifest["files"][path]


def test_stage121_policy_is_not_duplicated_or_modified() -> None:
    _, baseline, candidate = _prompts()
    assert candidate.user_prompt.count(CANDIDATE_POLICY) == 1
    assert candidate.user_prompt.replace("\n" + CANDIDATE_POLICY, "", 1) == baseline.user_prompt


def test_source_is_exact_stage10101_unit() -> None:
    source, _, _ = _prompts()
    assert len(source) == 575
    assert _sha_text(source) == "ac76cf63de96d465d23ed6a131fbc1008ed06adae76c8e0668b27e58cde1c2b5"


def test_request_configurations_differ_only_by_candidate_flag() -> None:
    baseline = _load("baseline_request.json")["request_configuration"]
    candidate = _load("candidate_request.json")["request_configuration"]
    assert baseline.pop("candidate_enabled") is False
    assert candidate.pop("candidate_enabled") is True
    assert baseline == candidate


@pytest.mark.parametrize("field,expected", [
    ("model", "meta/llama-3.3-70b-instruct"),
    ("timeout_seconds", 180),
    ("max_retries", 0),
    ("attempt_limit", 1),
    ("max_output_tokens", 800),
    ("chunk_size", 600),
    ("chunk_index", 1),
    ("provider", "nvidia"),
    ("profile", "literary"),
])
def test_frozen_request_setting(field: str, expected: object) -> None:
    assert _load("baseline_request.json")["request_configuration"][field] == expected
    assert _load("candidate_request.json")["request_configuration"][field] == expected


def test_empty_glossary_alias_and_previous_context_are_fixed() -> None:
    config = _load("baseline_request.json")["request_configuration"]
    assert config["locked_dictionary"] == {} and config["alias_map"] == {} and config["previous_context"] == ""


def test_profiles_match_actual_stage121_builder() -> None:
    _, baseline, candidate = _prompts()
    assert _load("baseline_prompt_profile.json")["total_tokens"] == baseline.prompt_profile.total_tokens
    assert _load("candidate_prompt_profile.json")["total_tokens"] == candidate.prompt_profile.total_tokens


@pytest.mark.parametrize("field", ["system_tokens", "context_tokens", "glossary_tokens", "source_tokens"])
def test_non_candidate_profile_tokens_are_identical(field: str) -> None:
    assert _load("baseline_prompt_profile.json")[field] == _load("candidate_prompt_profile.json")[field]


@pytest.mark.parametrize("field", ["system", "context", "glossary", "source_section"])
def test_non_candidate_component_hashes_are_identical(field: str) -> None:
    assert _load("baseline_prompt_profile.json")["component_sha256"][field] == _load("candidate_prompt_profile.json")["component_sha256"][field]


def test_only_policy_and_candidate_token_counts_change() -> None:
    baseline, candidate = _load("baseline_prompt_profile.json"), _load("candidate_prompt_profile.json")
    assert candidate["candidate_tokens"] - baseline["candidate_tokens"] == 109
    assert candidate["policy_tokens"] - baseline["policy_tokens"] == 109
    assert candidate["total_tokens"] - baseline["total_tokens"] == 109


def test_prompt_hashes_match_actual_builds() -> None:
    _, baseline, candidate = _prompts()
    assert _load("baseline_request.json")["user_prompt_sha256"] == _sha_text(baseline.user_prompt)
    assert _load("candidate_request.json")["user_prompt_sha256"] == _sha_text(candidate.user_prompt)
    assert _load("baseline_request.json")["system_prompt_sha256"] == _sha_text(baseline.system_prompt) == _sha_text(candidate.system_prompt)


def test_execution_package_has_exactly_two_planned_arms() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert set((package["baseline_configuration"], package["candidate_configuration"])[0]) >= {"request", "candidate_enabled"}
    assert package["comparison_variable"] == "candidate_enabled"


def test_execution_package_forbids_retry_and_rerun() -> None:
    retry = json.loads(PACKAGE.read_text(encoding="utf-8"))["frozen_configuration"]["retry"]
    assert retry == {"max_retries": 0, "attempt_limit": 1, "rerun_allowed": False}


@pytest.mark.parametrize("name", [
    "baseline_prompt_profile.json", "baseline_request.json", "baseline_response.json",
    "candidate_prompt_profile.json", "candidate_request.json", "candidate_response.json",
    "TE_V72_STAGE122_MANUAL_AB_REVIEW.json",
])
def test_expected_artifact_exists_and_is_in_package(name: str) -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    path = f"artifacts/te_v72_stage122/{name}"
    assert (ROOT / path).is_file() and path in package["expected_artifacts"]


@pytest.mark.parametrize("name", ["baseline_response.json", "candidate_response.json"])
def test_unexecuted_response_is_pending_without_translation(name: str) -> None:
    response = _load(name)
    assert response["status"] == "pending_execution"
    assert response["provider_executed"] is False and response["network_requests"] == 0
    assert response["translation_generated"] is False and response["response_text"] is None


def test_provider_execution_is_closed_without_authorization() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert package["authorization"]["explicit_real_provider_authorization_received"] is False
    assert package["authorization"]["execution_commands_enabled"] is False
    assert package["boundary"]["provider_executed"] is False and package["boundary"]["network_requests"] == 0


@pytest.mark.parametrize("field", [
    "unsupported_additions", "omissions", "meaning_distortion", "naturalness",
    "narrative_flow", "dialogue", "character_voice", "historical_tone", "terminology",
    "traditional_chinese", "blocking_defects", "overall_judgement", "review_comments",
])
def test_manual_review_field_is_unfilled(field: str) -> None:
    assert json.loads(REVIEW.read_text(encoding="utf-8"))["review"][field] is None


def test_manual_review_allowed_results_are_exact() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    assert review["allowed_overall_judgements"] == [
        "baseline_better", "candidate_better", "equivalent",
        "both_unacceptable", "insufficient_evidence",
    ]
    assert review["automated_judgement_allowed"] is False


def test_stage123_gate_requires_all_quality_conditions() -> None:
    gate = json.loads(REVIEW.read_text(encoding="utf-8"))["candidate_stage123_gate"]
    assert gate["all_conditions_required"] is True and gate["failure_result"] == "candidate_rejected"
    assert gate["naturalness_or_narrative_flow_human_improvement"] is None


def test_stage_boundary_is_fully_closed() -> None:
    boundary = json.loads(PACKAGE.read_text(encoding="utf-8"))["boundary"]
    assert all(value is False for key, value in boundary.items() if key != "network_requests")
    assert boundary["network_requests"] == 0 and boundary["stage123_started"] is False


def test_no_stage123_artifact_or_module_exists() -> None:
    assert not (ROOT / "artifacts/te_v72_stage123").exists()
    assert not any(ROOT.glob("*v720_stage123*"))
    assert not (ROOT / "core/te_v72_stage123").exists()
