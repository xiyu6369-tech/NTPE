from __future__ import annotations

import hashlib
import json

from core.name_resolution_contract_v72 import (
    NameResolutionRecord, apply_name_resolution_candidate, render_prompt_mappings,
    resolve_inventory, resolve_name, validate_name_output,
)
from tools.generate_te_v720_stage1259_name_resolution_contract_remediation import (
    CLAIM, EXPECTED_CLAIM_SHA256, EXPECTED_RESPONSE_SHA256, RESPONSE, fixed_records,
)


def approved(source: str, target: str, mapping_source: str, evidence: str) -> NameResolutionRecord:
    return NameResolutionRecord.create(
        source_name=source, approved_zh_hant_name=target,
        mapping_status="approved_target_mapping", mapping_source=mapping_source,
        evidence_ids=(evidence,), approval_status="approved",
    )


def test_resolution_chain_glossary_corpus_character_memory_priority() -> None:
    items = (
        approved("정태의", "鄭泰義", "character_memory", "memory"),
        approved("정태의", "鄭泰義", "corpus", "corpus"),
        approved("정태의", "鄭泰義", "glossary", "glossary"),
    )
    assert resolve_name("정태의", items).mapping_source == "glossary"


def test_conflict_across_sources_is_fail_closed() -> None:
    result = resolve_name("정태의", (
        approved("정태의", "鄭泰義", "glossary", "glossary"),
        approved("정태의", "鄭太義", "corpus", "corpus"),
    ))
    assert result.mapping_status == "conflicting_target_mapping"
    assert result.prompt_eligible is False


def test_mixed_eligible_unresolved_prompt_rendering() -> None:
    records = (approved("정태의", "鄭泰義", "glossary", "glossary"), *fixed_records())
    text, evidence = render_prompt_mappings(records, token_budget=64)
    assert "- 정태의 → 鄭泰義" in text
    assert "영희 →" not in text and "민수 →" not in text
    assert set(evidence.unresolved_names) == {"영희", "민수"}


def test_budget_limited_rendering_keeps_first_approved_mapping() -> None:
    records = (
        approved("정태의", "鄭泰義", "glossary", "a"),
        approved("김선아", "金善雅", "glossary", "b"),
    )
    text, evidence = render_prompt_mappings(
        records,
        source_first_occurrence={
            records[0].normalized_source_name: 0, records[1].normalized_source_name: 1,
        },
        token_budget=4,
    )
    assert "정태의" in text and "김선아" not in text
    assert evidence.budget_exhausted is True


def test_literary_prompt_is_byte_equivalent_when_disabled() -> None:
    original = "【Policy】原始 Literary Prompt"
    result = apply_name_resolution_candidate(original, fixed_records(), enabled=False)
    assert result.prompt.encode("utf-8") == original.encode("utf-8")


def test_stage1258_raw_response_classification() -> None:
    response = json.loads(RESPONSE.read_text(encoding="utf-8"))
    source = "영희가 민수와 선생님을 번갈아 보며 말했다. ‘선생님, 민수 씨도 함께 가실까요?’"
    result = validate_name_output(response["raw_response"], source_text=source, records=fixed_records())
    assert "proper_name_hangul_residual" in result.classifications
    assert "partial_name_normalization" in result.classifications
    assert result.mixed_language_inline_output is True


def test_no_provider_network_or_runtime_side_effects() -> None:
    result = apply_name_resolution_candidate("ORIGINAL", fixed_records(), enabled=False)
    assert result.provider_payload_changed is False
    assert result.production_hook_count_added == 0
    assert result.runtime_request_path_modified is False


def test_historical_artifacts_are_read_only() -> None:
    claim_before, response_before = CLAIM.read_bytes(), RESPONSE.read_bytes()
    resolve_inventory(("영희", "민수"), fixed_records())
    assert hashlib.sha256(claim_before).hexdigest() == EXPECTED_CLAIM_SHA256
    assert hashlib.sha256(response_before).hexdigest() == EXPECTED_RESPONSE_SHA256
    assert CLAIM.read_bytes() == claim_before and RESPONSE.read_bytes() == response_before
