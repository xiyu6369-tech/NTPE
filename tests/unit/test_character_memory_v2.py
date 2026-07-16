from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

import core.character_memory_v2 as cm2
from core.character_memory_v2 import (
    AddDisposition,
    ApprovalMetadata,
    ApprovalStatus,
    CharacterMemoryValidationError,
    EvidenceType,
    ExpiryKind,
    ExpiryPolicy,
    FactType,
    MemoryStatus,
    MemoryStore,
    add_or_merge_memory,
    approve_memory,
    create_evidence,
    create_memory,
    deserialize_memory_store,
    expire_memory,
    reject_memory,
    rollback_memory,
    select_prompt_eligible_memories,
    serialize_memory_store,
)


T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"
T2 = "2026-07-16T00:02:00Z"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence(kind: EvidenceType | str = EvidenceType.SOURCE_OBSERVATION, *, case: str = "case-1", segment: str = "seg-1", excerpt: str = "人物直接證據"):
    return create_evidence(
        evidence_type=kind,
        source_case_id=case,
        source_segment_id=segment,
        source_text_hash=sha(case + segment + excerpt),
        excerpt=excerpt,
        language="ko",
        observed_at=T0,
    )


def memory(value: str = "已知人物事實", *, kind: EvidenceType | str = EvidenceType.SOURCE_OBSERVATION, fact_type: FactType | str = FactType.ROLE_OR_IDENTITY, character_id: str = "char-1", segment: str = "seg-1", confidence: float = 0.95, expiry: ExpiryPolicy | None = None):
    ev = evidence(kind, segment=segment, excerpt=value)
    return create_memory(
        character_id=character_id,
        fact_type=fact_type,
        value=value,
        evidence=ev,
        confidence=confidence,
        created_at=T0,
        expiry_policy=expiry,
    )


def approved_memory(value: str, *, segment: str) -> cm2.MemoryRecord:
    ev = evidence(EvidenceType.HUMAN_APPROVED, segment=segment, excerpt=value)
    return create_memory(
        character_id="char-1",
        fact_type=FactType.CANONICAL_NAME,
        value=value,
        evidence=ev,
        confidence=0.8,
        approval_status=ApprovalStatus.APPROVED,
        approval_metadata=ApprovalMetadata(value, T0, "reviewer", "decision-1"),
        created_at=T0,
    )


def test_observed_inference_and_human_approval_are_separate():
    store = MemoryStore()
    observed = memory()
    inferred = memory("推測的人物特質", kind=EvidenceType.AI_INFERENCE, fact_type=FactType.PERSONALITY_TRAIT, segment="seg-2")
    add_or_merge_memory(store, observed, now=T0)
    add_or_merge_memory(store, inferred, now=T0)
    approved = approve_memory(store, observed.memory_id, approved_at=T1, reviewer="human")
    assert inferred.evidence_type == EvidenceType.AI_INFERENCE
    assert approved.evidence_type == EvidenceType.HUMAN_APPROVED
    assert approved.approval_status == ApprovalStatus.APPROVED
    assert inferred.approval_status == ApprovalStatus.PENDING


def test_confidence_is_not_approval_and_ai_inference_is_excluded_by_default():
    store = MemoryStore()
    inferred = memory("高信心推論", kind=EvidenceType.AI_INFERENCE, fact_type=FactType.PERSONALITY_TRAIT, confidence=0.99)
    add_or_merge_memory(store, inferred, now=T0)
    assert inferred.approval_status == ApprovalStatus.PENDING
    assert not select_prompt_eligible_memories(store, now=T1).items
    assert select_prompt_eligible_memories(store, include_pending=True, now=T1).items


def test_human_approved_is_prompt_eligible_even_with_lower_confidence():
    store = MemoryStore()
    record = approved_memory("鄭泰義", segment="seg-approved")
    add_or_merge_memory(store, record, now=T0)
    assert [item.value for item in select_prompt_eligible_memories(store, confidence_threshold=0.95, now=T1).items] == ["鄭泰義"]


def test_exact_and_unicode_whitespace_duplicates_do_not_append():
    store = MemoryStore()
    first = memory("Ａ  B")
    equivalent = memory("A B")
    assert add_or_merge_memory(store, first, now=T0).disposition == AddDisposition.ACCEPTED
    assert add_or_merge_memory(store, equivalent, now=T1).disposition == AddDisposition.MERGED
    assert len(store.records) == 1


def test_different_evidence_merges_into_same_canonical_fact():
    store = MemoryStore()
    first = memory("固定身分", segment="seg-1")
    second = memory("固定身分", segment="seg-2")
    add_or_merge_memory(store, first, now=T0)
    result = add_or_merge_memory(store, second, now=T1)
    assert result.disposition == AddDisposition.MERGED
    assert len(store.records) == 1
    assert len(result.record.evidence) == 2
    assert result.record.version == 2


def test_different_value_is_visible_conflict_not_merge():
    store = MemoryStore()
    first = memory("醫師", segment="seg-1")
    second = memory("律師", segment="seg-2")
    add_or_merge_memory(store, first, now=T0)
    result = add_or_merge_memory(store, second, now=T1)
    assert result.disposition == AddDisposition.CONFLICT
    assert result.conflict and result.conflict.unresolved
    assert len(store.records) == 2
    assert not select_prompt_eligible_memories(store, now=T2).items


def test_human_approved_value_rejects_conflicting_ai_inference():
    store = MemoryStore()
    approved = approved_memory("鄭泰義", segment="seg-a")
    add_or_merge_memory(store, approved, now=T0)
    inferred = memory("正太義", kind=EvidenceType.AI_INFERENCE, fact_type=FactType.CANONICAL_NAME, segment="seg-b")
    result = add_or_merge_memory(store, inferred, now=T1)
    assert result.disposition == AddDisposition.REJECTED
    assert result.conflict and result.conflict.preferred_memory_id == approved.memory_id
    assert [item.value for item in select_prompt_eligible_memories(store, now=T2).items] == ["鄭泰義"]


def test_two_approved_values_require_explicit_resolution():
    store = MemoryStore()
    one = approved_memory("鄭泰義", segment="seg-a")
    two = approved_memory("鄭太義", segment="seg-b")
    add_or_merge_memory(store, one, now=T0)
    result = add_or_merge_memory(store, two, now=T1)
    assert result.disposition == AddDisposition.CONFLICT
    assert result.conflict and result.conflict.unresolved
    assert not select_prompt_eligible_memories(store, now=T2).items


def test_approved_correction_supersedes_without_silent_overwrite():
    store = MemoryStore()
    old = approved_memory("舊譯名", segment="seg-old")
    pending = memory("新譯名", fact_type=FactType.CANONICAL_NAME, segment="seg-new")
    add_or_merge_memory(store, old, now=T0)
    add_or_merge_memory(store, pending, now=T1)
    corrected = approve_memory(store, pending.memory_id, approved_at=T2, reviewer="human", decision_reference="decision-2", supersede_memory_id=old.memory_id)
    assert corrected.approval_status == ApprovalStatus.APPROVED
    assert store.get(old.memory_id).status == MemoryStatus.SUPERSEDED
    assert [item.value for item in select_prompt_eligible_memories(store, now="2026-07-16T00:03:00Z").items] == ["新譯名"]


def test_expired_and_wrong_segment_scope_are_ineligible():
    store = MemoryStore()
    record = memory("當下受傷", fact_type=FactType.TEMPORAL_STATE, expiry=ExpiryPolicy(ExpiryKind.SEGMENT_SCOPE, scope_id="seg-1"))
    add_or_merge_memory(store, record, now=T0)
    assert select_prompt_eligible_memories(store, scope={"segment_id": "seg-1"}, now=T1).items
    assert not select_prompt_eligible_memories(store, scope={"segment_id": "seg-2"}, now=T1).items
    expire_memory(store, record.memory_id, expired_at=T2)
    assert not select_prompt_eligible_memories(store, scope={"segment_id": "seg-1"}, now="2026-07-16T00:03:00Z").items


def test_permanent_fact_survives_session_scope_and_temporal_default_is_not_never():
    permanent = memory("長期身分")
    temporal = memory("暫時疲倦", fact_type=FactType.TEMPORAL_STATE)
    assert permanent.expiry_policy.kind == ExpiryKind.NEVER
    assert temporal.expiry_policy.kind == ExpiryKind.MANUAL_REVIEW_REQUIRED


def test_token_budget_zero_small_normal_and_deterministic():
    store = MemoryStore()
    for index in range(8):
        add_or_merge_memory(store, memory(f"人物事實 {index}", fact_type=FactType.OTHER, segment=f"seg-{index}"), now=T0)
    assert not select_prompt_eligible_memories(store, token_budget=0, now=T1).items
    small = select_prompt_eligible_memories(store, token_budget=10, now=T1)
    normal1 = select_prompt_eligible_memories(store, token_budget=256, now=T1)
    normal2 = select_prompt_eligible_memories(store, token_budget=256, now=T1)
    assert small.estimated_tokens <= 10
    assert normal1.estimated_tokens <= 256
    assert normal1 == normal2
    with pytest.raises(CharacterMemoryValidationError):
        select_prompt_eligible_memories(store, token_budget=-1, now=T1)


def test_approved_fact_is_not_displaced_by_lower_priority_inference():
    store = MemoryStore()
    approved = approved_memory("核准姓名", segment="seg-approved")
    add_or_merge_memory(store, approved, now=T0)
    for index in range(10):
        add_or_merge_memory(store, memory(f"推論 {index}", kind=EvidenceType.AI_INFERENCE, fact_type=FactType.OTHER, segment=f"seg-i-{index}"), now=T0)
    selected = select_prompt_eligible_memories(store, token_budget=12, include_pending=True, now=T1)
    assert selected.items[0].memory_id == approved.memory_id
    assert selected.estimated_tokens <= 12


def test_rollback_update_restores_prior_value_properties_and_preserves_evidence():
    store = MemoryStore()
    first = memory("固定身分", segment="seg-1", confidence=0.8)
    second = memory("固定身分", segment="seg-2", confidence=0.99)
    add_or_merge_memory(store, first, now=T0)
    add_or_merge_memory(store, second, now=T1)
    restored = rollback_memory(store, first.memory_id, rolled_back_at=T2)
    assert restored.confidence == 0.8
    assert restored.version == 3
    assert len(restored.evidence) == 2
    assert store.history[first.memory_id]


def test_rollback_approved_correction_restores_old_approved_memory():
    store = MemoryStore()
    old = approved_memory("舊核准值", segment="seg-old")
    new = memory("新核准值", fact_type=FactType.CANONICAL_NAME, segment="seg-new")
    add_or_merge_memory(store, old, now=T0)
    add_or_merge_memory(store, new, now=T1)
    approve_memory(store, new.memory_id, approved_at=T2, decision_reference="decision-2", supersede_memory_id=old.memory_id)
    rolled = rollback_memory(store, new.memory_id, rolled_back_at="2026-07-16T00:03:00Z")
    assert rolled.status == MemoryStatus.ROLLED_BACK
    assert store.get(old.memory_id).status == MemoryStatus.ACTIVE
    assert [item.value for item in select_prompt_eligible_memories(store, now="2026-07-16T00:04:00Z").items] == ["舊核准值"]


def test_invalid_rollback_is_fail_closed_and_does_not_mutate_store():
    store = MemoryStore()
    record = memory()
    add_or_merge_memory(store, record, now=T0)
    before = serialize_memory_store(store)
    with pytest.raises(CharacterMemoryValidationError):
        rollback_memory(store, record.memory_id, target_version=99, rolled_back_at=T1)
    assert serialize_memory_store(store) == before


def test_serialization_round_trip_and_canonical_output_are_deterministic():
    store = MemoryStore()
    add_or_merge_memory(store, memory(), now=T0)
    encoded = serialize_memory_store(store)
    restored = deserialize_memory_store(encoded)
    assert serialize_memory_store(restored) == encoded
    assert json.loads(encoded)["schema_version"] == "2.0"


@pytest.mark.parametrize("payload", ["{", "[]", "not json"])
def test_malformed_serialization_is_rejected(payload):
    with pytest.raises(CharacterMemoryValidationError):
        deserialize_memory_store(payload)


def test_unknown_schema_invalid_confidence_and_status_are_rejected():
    store = MemoryStore()
    record = memory()
    add_or_merge_memory(store, record, now=T0)
    data = json.loads(serialize_memory_store(store))
    data["schema_version"] = "999"
    with pytest.raises(CharacterMemoryValidationError):
        deserialize_memory_store(json.dumps(data))
    data = json.loads(serialize_memory_store(store))
    data["records"][0]["confidence"] = 2.0
    with pytest.raises(CharacterMemoryValidationError):
        deserialize_memory_store(json.dumps(data))
    data = json.loads(serialize_memory_store(store))
    data["records"][0]["status"] = "unknown"
    with pytest.raises(CharacterMemoryValidationError):
        deserialize_memory_store(json.dumps(data))


def test_secret_like_memory_content_is_rejected():
    ev = evidence(excerpt="safe placeholder")
    with pytest.raises(CharacterMemoryValidationError):
        create_memory(character_id="char-1", fact_type="other", value="Author" + "ization: populated-token-value", evidence=ev, confidence=0.9, created_at=T0)


def test_name_safety_has_no_auto_completion_or_transliteration():
    unresolved = memory("박", fact_type=FactType.NAME_VARIANT, character_id="unresolved:name-1")
    store = MemoryStore()
    add_or_merge_memory(store, unresolved, now=T0)
    assert store.get(unresolved.memory_id).character_id == "unresolved:name-1"
    assert not select_prompt_eligible_memories(store, now=T1).items
    assert not {"transliterate_name", "auto_complete_name", "extract_character"} & set(cm2.__all__)
    with pytest.raises(CharacterMemoryValidationError):
        memory("普通名詞", character_id="")


def test_name_variant_requires_structured_evidence_and_canonical_unresolved_fails_closed():
    with pytest.raises(CharacterMemoryValidationError):
        create_memory(character_id="char-1", fact_type="name_variant", value="別名", evidence=(), confidence=0.9, created_at=T0)
    ev = evidence(excerpt="未解析姓名")
    with pytest.raises(CharacterMemoryValidationError):
        create_memory(character_id="unresolved:name-2", fact_type="canonical_name", value="自動完整姓名", evidence=ev, confidence=0.99, created_at=T0)


def test_selection_fails_closed_for_directly_tampered_store_record():
    store = MemoryStore()
    record = memory()
    add_or_merge_memory(store, record, now=T0)
    store.records[record.memory_id] = replace(record, confidence=2.0)
    selected = select_prompt_eligible_memories(store, now=T1)
    assert not selected.items
    assert selected.excluded_counts["invalid"] == 1


def test_rejected_decision_is_not_resurrected_by_duplicate_import():
    store = MemoryStore()
    record = memory("已拒絕候選")
    add_or_merge_memory(store, record, now=T0)
    reject_memory(store, record.memory_id, rejected_at=T1, decision_reference="reject-1")
    result = add_or_merge_memory(store, record, now=T2)
    assert result.disposition == AddDisposition.REJECTED
    assert store.get(record.memory_id).status == MemoryStatus.REJECTED
