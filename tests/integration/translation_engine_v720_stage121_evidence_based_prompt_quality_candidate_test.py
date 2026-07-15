from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.literary import LiteraryPromptBuilder
from core.literary_prompt_quality_candidate_v72 import CANDIDATE_POLICY, FEATURE_FLAG, build_literary_prompt

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "정태의는 난감해하고 있었다. 카일이 말했다."
GLOSSARY = {"정태의": "鄭泰義", "카일": "凱爾"}
PREVIOUS = "두 사람은 여행지에 도착했다."


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _build(enabled: bool = False):
    return build_literary_prompt(
        chunk_text=SOURCE, locked_dictionary=GLOSSARY,
        previous_context=PREVIOUS, candidate_enabled=enabled,
    )


def _baseline():
    return LiteraryPromptBuilder().build(
        chunk_text=SOURCE, locked_dictionary=GLOSSARY, previous_context=PREVIOUS,
    )


def test_candidate_default_disabled() -> None:
    result = build_literary_prompt(chunk_text=SOURCE, locked_dictionary=GLOSSARY)
    assert result.candidate_enabled is False and result.prompt_profile.candidate_tokens == 0


def test_disabled_prompt_is_byte_equivalent_to_frozen_builder() -> None:
    assert _build().user_prompt == _baseline().user_prompt


def test_disabled_prompt_dictionary_matches_baseline() -> None:
    candidate = _build().to_prompt_dict()
    baseline = _baseline().to_prompt_dict()
    candidate["prompt_profile"] = {key: candidate["prompt_profile"][key] for key in baseline["prompt_profile"]}
    candidate["prompt_compiler"] = {key: candidate["prompt_compiler"][key] for key in baseline["prompt_compiler"]}
    assert candidate == baseline


def test_enabled_adds_exactly_one_candidate_policy() -> None:
    enabled = _build(True)
    assert enabled.user_prompt.count(CANDIDATE_POLICY) == 1
    assert enabled.user_prompt.replace("\n" + CANDIDATE_POLICY, "", 1) == _baseline().user_prompt


def test_system_prompt_unchanged() -> None:
    assert _build(True).system_prompt == _baseline().system_prompt


@pytest.mark.parametrize("attribute", ["narrative_context", "character_context", "glossary_context"])
def test_structured_contexts_unchanged(attribute: str) -> None:
    assert getattr(_build(True), attribute).to_dict() == getattr(_baseline(), attribute).to_dict()


@pytest.mark.parametrize("section", ["【Korean】", "【Output】"])
def test_source_and_output_sections_unchanged(section: str) -> None:
    baseline = _baseline().user_prompt.split(section, 1)[1]
    candidate = _build(True).user_prompt.split(section, 1)[1]
    assert candidate == baseline


def test_context_source_and_glossary_hashes_unchanged() -> None:
    baseline, enabled = _baseline(), _build(True)
    assert _sha(baseline.narrative_context.render()) == _sha(enabled.narrative_context.render())
    assert _sha(baseline.character_context.render()) == _sha(enabled.character_context.render())
    assert _sha(baseline.glossary_context.render()) == _sha(enabled.glossary_context.render())
    assert _sha(SOURCE) == _sha(SOURCE)


@pytest.mark.parametrize("field", ["system_tokens", "context_tokens", "glossary_tokens", "source_tokens"])
def test_non_policy_token_profiles_unchanged(field: str) -> None:
    assert getattr(_build(True).prompt_profile, field) == getattr(_baseline().prompt_profile, field)


def test_candidate_profile_is_observable_and_bounded() -> None:
    profile = _build(True).prompt_profile
    assert profile.candidate_enabled and 0 < profile.candidate_tokens <= 120
    assert profile.candidate_chars == len(CANDIDATE_POLICY)


def test_candidate_profile_delta_is_exact() -> None:
    baseline, enabled = _baseline().prompt_profile, _build(True).prompt_profile
    assert enabled.total_tokens - baseline.total_tokens == enabled.candidate_tokens
    assert enabled.total_chars - baseline.total_chars == enabled.candidate_chars


def test_candidate_is_deterministic() -> None:
    assert _build(True).to_prompt_dict() == _build(True).to_prompt_dict()


def test_candidate_can_be_fully_rolled_back() -> None:
    assert _build(True).user_prompt != _build(False).user_prompt
    assert _build(False).user_prompt == _baseline().user_prompt


@pytest.mark.parametrize("phrase", [
    "僅翻譯原文明示", "含混處保持含混", "不摘要、刪節、合併或漏譯",
    "自然流暢", "不沿用生硬韓文語序", "依時代、場景、視角、身分與關係選詞",
    "不強套現代台灣口語", "保留禮貌、距離、情緒、權力關係與角色口吻",
    "不補全名", "對話用「」",
])
def test_required_quality_rule_is_present(phrase: str) -> None:
    assert phrase in CANDIDATE_POLICY


@pytest.mark.parametrize("defect", [
    "unsupported detail", "omission/completeness", "literal or unnatural phrasing",
    "narrative naturalness", "character voice", "historical/contextual tone",
])
def test_static_evidence_coverage(defect: str) -> None:
    mapping = {
        "unsupported detail": "不補時間、數量、因果、動機、關係、地點、動作或背景",
        "omission/completeness": "不摘要、刪節、合併或漏譯",
        "literal or unnatural phrasing": "不沿用生硬韓文語序",
        "narrative naturalness": "自然流暢",
        "character voice": "角色口吻",
        "historical/contextual tone": "依時代、場景、視角、身分與關係選詞",
    }
    assert mapping[defect] in CANDIDATE_POLICY


def test_feature_flag_name_and_default_are_explicit() -> None:
    assert FEATURE_FLAG == "--quality-candidate-v72" and _build().candidate_enabled is False


def test_no_provider_or_runtime_settings_are_part_of_candidate_payload() -> None:
    payload = _build(True).to_prompt_dict()
    assert not ({"model", "timeout", "retry", "chunk_size", "max_output_tokens"} & payload.keys())


def test_execution_package_keeps_frozen_provider_settings() -> None:
    package = json.loads((ROOT / "artifacts/te_v72_stage121/TE_V72_STAGE121_PROVIDER_EXECUTION_PACKAGE.json").read_text(encoding="utf-8"))
    settings = package["provider_settings"]
    assert settings == {"model":"meta/llama-3.3-70b-instruct", "timeout_seconds":180, "attempt_limit":1, "max_output_tokens":800, "chunk_size":600}


def test_execution_package_is_non_executing() -> None:
    package = json.loads((ROOT / "artifacts/te_v72_stage121/TE_V72_STAGE121_PROVIDER_EXECUTION_PACKAGE.json").read_text(encoding="utf-8"))
    assert package["expected_request_count"] == 2
    assert package["provider_executed"] is False and package["network_requests"] == 0


def test_stage_artifact_preserves_quality_claim_boundary() -> None:
    artifact = json.loads((ROOT / "artifacts/te_v72_stage121/TE_V72_STAGE121_EVIDENCE_BASED_PROMPT_QUALITY_CANDIDATE.json").read_text(encoding="utf-8"))
    assert artifact["quality_claim"] == {"translation_quality_improved":False, "quality_improvement_verified":False, "comparison_executed":False, "candidate_status":"prepared_not_validated"}


def test_no_golden_corpus_mutation_or_new_translation_claim() -> None:
    artifact = json.loads((ROOT / "artifacts/te_v72_stage121/TE_V72_STAGE121_EVIDENCE_BASED_PROMPT_QUALITY_CANDIDATE.json").read_text(encoding="utf-8"))
    assert artifact["boundary"]["golden_corpus_modified"] is False
    assert artifact["boundary"]["new_translation_generated"] is False


def test_stage_11_plans_remain_unmodified_and_not_applied() -> None:
    plan = json.loads((ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json").read_text(encoding="utf-8"))
    assert plan["plans_applied"] == 0 and all(row["implementation_status"] == "planned_not_applied" for row in plan["plans"])
