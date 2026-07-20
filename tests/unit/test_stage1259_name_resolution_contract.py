from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.name_resolution_contract_v72 import (
    DEFAULT_ENABLED, NameResolutionRecord, apply_name_resolution_candidate,
    canonical_json, is_prompt_eligible, mapping_exclusion_reasons,
    render_prompt_mappings, resolve_name, validate_name_output,
)
from tools.generate_te_v720_stage1259_name_resolution_contract_remediation import (
    CLAIM, EXPECTED_CLAIM_SHA256, EXPECTED_RESPONSE_SHA256, RESPONSE,
    build_artifacts, fixed_records,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "영희가 민수와 선생님을 번갈아 보며 말했다."


def record(
    target: str | None,
    *,
    source: str = "정태의",
    mapping_source: str = "glossary",
    status: str = "approved_target_mapping",
    approval: str = "approved",
    evidence: tuple[str, ...] = ("evidence-1",),
    superseded: bool = False,
    expired: bool = False,
) -> NameResolutionRecord:
    return NameResolutionRecord.create(
        source_name=source, approved_zh_hant_name=target,
        mapping_status=status, mapping_source=mapping_source,
        approval_status=approval, evidence_ids=evidence,
        superseded=superseded, expired=expired,
    )


def test_romanization_is_not_approved_target_mapping() -> None:
    item = NameResolutionRecord.create(
        source_name="영희", identity_transliteration="Yeong-hui",
        mapping_status="identity_only", mapping_source="character_memory",
        approval_status="approved", evidence_ids=("char-yeonghui",),
    )
    assert item.prompt_eligible is False
    assert "not_approved_target_mapping" in mapping_exclusion_reasons(item)


@pytest.mark.parametrize("target", ["영희", "Yeong-hui", "民수", "英희", "Yeong희"])
def test_invalid_target_scripts_are_rejected(target: str) -> None:
    item = record(target)
    assert item.prompt_eligible is False
    assert mapping_exclusion_reasons(item)


def test_approved_zh_hant_mapping_is_accepted() -> None:
    item = record("鄭泰義")
    assert item.target_script_valid is True
    assert is_prompt_eligible(item) is True


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"status": "rejected_target_mapping", "approval": "rejected"}, "rejected_mapping"),
        ({"status": "expired_target_mapping", "expired": True}, "expired_mapping"),
        ({"superseded": True}, "superseded_mapping"),
    ],
)
def test_rejected_expired_and_superseded_mappings_are_excluded(kwargs: dict[str, object], reason: str) -> None:
    item = record("鄭泰義", **kwargs)
    assert is_prompt_eligible(item) is False
    assert reason in mapping_exclusion_reasons(item)


def test_conflicting_approved_mappings_fail_closed_without_first_match() -> None:
    first = record("鄭泰義", mapping_source="glossary")
    second = record("鄭太義", mapping_source="corpus")
    resolved = resolve_name("정태의", (first, second))
    assert resolved.mapping_status == "conflicting_target_mapping"
    assert resolved.prompt_eligible is False and resolved.conflict_state is True
    assert resolved.approved_zh_hant_name is None


def test_no_inferred_chinese_name() -> None:
    resolved = resolve_name("민수", ())
    assert resolved.approved_zh_hant_name is None
    assert resolved.mapping_status == "missing_approved_target_name"


def test_fixed_yeonghui_and_minsu_results() -> None:
    yeonghui, minsu = fixed_records()
    assert yeonghui.mapping_status == "identity_only"
    assert yeonghui.identity_transliteration == "Yeong-hui"
    assert yeonghui.approved_zh_hant_name is None and yeonghui.prompt_eligible is False
    assert minsu.mapping_status == "missing_approved_target_name"
    assert minsu.identity_transliteration is None and minsu.approved_zh_hant_name is None
    assert minsu.unresolved_reason == "no_authoritative_target_mapping"


@pytest.mark.parametrize(
    ("mapping_source", "expected_source"),
    [("glossary", "glossary"), ("corpus", "corpus"), ("character_memory", "character_memory")],
)
def test_valid_approved_source_mappings(mapping_source: str, expected_source: str) -> None:
    item = record("鄭泰義", mapping_source=mapping_source)
    assert resolve_name("정태의", (item,)).mapping_source == expected_source


def test_glossary_priority_over_same_approved_corpus_and_character_mapping() -> None:
    items = (
        record("鄭泰義", mapping_source="character_memory", evidence=("memory",)),
        record("鄭泰義", mapping_source="corpus", evidence=("corpus",)),
        record("鄭泰義", mapping_source="glossary", evidence=("glossary",)),
    )
    assert resolve_name("정태의", items).mapping_source == "glossary"


def test_identity_and_unresolved_are_not_rendered_or_budgeted() -> None:
    yeonghui, minsu = fixed_records()
    text, evidence = render_prompt_mappings((yeonghui, minsu), token_budget=64)
    assert text == "" and evidence.token_estimate == 0
    assert evidence.rendered_mappings == ()
    assert set(evidence.unresolved_names) == {"영희", "민수"}


def test_approved_mapping_rendering_is_deterministic() -> None:
    first = record("鄭泰義")
    second = record("金善雅", source="김선아", evidence=("evidence-2",))
    a = render_prompt_mappings((second, first), source_first_occurrence={
        first.normalized_source_name: 0, second.normalized_source_name: 1,
    })
    b = render_prompt_mappings((first, second), source_first_occurrence={
        first.normalized_source_name: 0, second.normalized_source_name: 1,
    })
    assert a == b
    assert a[0].splitlines()[1] == "- 정태의 → 鄭泰義"


def test_budget_prioritizes_approved_and_reports_exhaustion() -> None:
    first = record("鄭泰義")
    second = record("金善雅", source="김선아", evidence=("evidence-2",))
    text, evidence = render_prompt_mappings(
        (second, first),
        source_first_occurrence={first.normalized_source_name: 0, second.normalized_source_name: 1},
        token_budget=4,
    )
    assert "정태의" in text and "김선아" not in text
    assert evidence.budget_exhausted is True


@pytest.mark.parametrize(
    ("output", "classification", "subtype"),
    [
        ("영희", "proper_name_hangul_residual", "full_hangul_proper_name_residual"),
        ("民수", "partial_name_normalization", "mixed_han_hangul_name"),
        ("英희", "mixed_script_proper_name", "mixed_han_hangul_name"),
        ("Yeong희", "mixed_script_proper_name", "mixed_latin_hangul_name"),
        ("민Su", "mixed_script_proper_name", "mixed_latin_hangul_name"),
        ("鄭태의", "mixed_script_proper_name", "mixed_han_hangul_name"),
    ],
)
def test_extended_output_classification(output: str, classification: str, subtype: str) -> None:
    result = validate_name_output(output, source_text=SOURCE, records=fixed_records())
    assert classification in result.classifications
    assert subtype in result.failure_subtypes
    assert result.validate_only is True and result.repair_applied is False
    assert result.provider_request is False


def test_approved_name_mapping_violation_detection() -> None:
    approved = record("鄭泰義")
    result = validate_name_output("정태의來了。", source_text="정태의가 왔다.", records=(approved,))
    assert "approved_name_mapping_violation" in result.classifications


def test_source_echo_remains_separate() -> None:
    result = validate_name_output(SOURCE, source_text=SOURCE, records=fixed_records())
    assert "source_echo" in result.classifications
    assert "proper_name_hangul_residual" in result.classifications


def test_validator_never_repairs_output() -> None:
    original = "民수仍在場。"
    result = validate_name_output(original, source_text=SOURCE, records=fixed_records())
    assert result.repair_applied is False
    assert original == "民수仍在場。"


def test_default_candidate_is_disabled_and_prompt_payload_unchanged() -> None:
    result = apply_name_resolution_candidate("ORIGINAL", fixed_records())
    assert DEFAULT_ENABLED is False and result.enabled is False
    assert result.prompt == "ORIGINAL" and result.prompt_changed is False
    assert result.provider_payload_changed is False
    assert result.production_hook_count_added == 0
    assert result.runtime_request_path_modified is False


def test_deterministic_serialization() -> None:
    left = canonical_json({"b": 2, "a": 1})
    right = canonical_json({"a": 1, "b": 2})
    assert left == right


def test_artifacts_are_deterministic_secret_free_and_offline() -> None:
    first, second = build_artifacts(), build_artifacts()
    assert first == second
    raw = b"".join(first.values()).lower()
    assert b"bearer " not in raw and b"x-api-key" not in raw and b"api_key" not in raw
    summary = json.loads(first[next(path for path in first if path.name == "preparation_summary.json")])
    assert summary["provider_requests"] == 0 and summary["network_requests"] == 0


def test_historical_claim_response_and_gate_are_unchanged() -> None:
    claim, response = CLAIM.read_bytes(), RESPONSE.read_bytes()
    assert hashlib.sha256(claim).hexdigest() == EXPECTED_CLAIM_SHA256
    assert hashlib.sha256(response).hexdigest() == EXPECTED_RESPONSE_SHA256
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    assert artifacts["activation_contract.json"]["activation_gate"] == (
        "translation_quality_integration_ready_for_controlled_canary"
    )
    assert CLAIM.read_bytes() == claim and RESPONSE.read_bytes() == response
