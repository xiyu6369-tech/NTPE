from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

import core.context_scene_memory as csm


T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"
T2 = "2026-07-16T00:02:00Z"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence(kind=csm.EvidenceType.SOURCE_OBSERVATION, *, segment="seg-1", excerpt="原文證據"):
    kwargs = {"source_text_hash": sha("src:" + segment)}
    if kind == csm.EvidenceType.TRANSLATION_OBSERVATION:
        kwargs = {"translation_text_hash": sha("tr:" + segment)}
    return csm.create_context_evidence(
        evidence_type=kind, source_case_id="case-1", source_segment_id=segment,
        excerpt=excerpt, language="ko", observed_at=T0, **kwargs,
    )


def context(value="狀態", *, kind=csm.ContextType.OTHER, evidence_kind=csm.EvidenceType.SOURCE_OBSERVATION,
            segment="seg-1", scene="scene-1", chapter="chapter-1", sequence=1, confidence=.95,
            approval=csm.ApprovalStatus.PENDING, expiry=None, experimental=False):
    ev = evidence(evidence_kind, segment=segment, excerpt=value)
    return csm.create_context_memory(
        context_type=kind, value=value, evidence=ev, confidence=confidence,
        scene_id=scene, chapter_id=chapter, sequence_index=sequence,
        approval_status=approval, expiry_policy=expiry, created_at=T0,
        experimental_only=experimental,
    )


def scene(store=None, scene_id="scene-1", chapter_id="chapter-1"):
    store = store or csm.ContextMemoryStore()
    csm.add_scene(store, csm.create_scene_memory(scene_id=scene_id, chapter_id=chapter_id, evidence=evidence(), created_at=T0))
    return store


def test_schema_and_evidence_types_are_separate():
    source = evidence(csm.EvidenceType.SOURCE_OBSERVATION)
    translation = evidence(csm.EvidenceType.TRANSLATION_OBSERVATION, segment="seg-2")
    assert csm.SCHEMA_VERSION == "1.0"
    assert source.source_text_hash and not source.translation_text_hash
    assert translation.translation_text_hash and not translation.source_text_hash


def test_missing_evidence_rule_id_and_oversized_excerpt_fail_closed():
    with pytest.raises(csm.ContextSceneValidationError):
        csm.create_context_memory(context_type="other", value="x", evidence=(), confidence=.9, created_at=T0)
    with pytest.raises(csm.ContextSceneValidationError):
        evidence(csm.EvidenceType.RULE_DERIVED)
    with pytest.raises(csm.ContextSceneValidationError):
        evidence(excerpt="x" * 513)


def test_previous_translation_is_bounded_and_requires_translation_evidence():
    previous = context("上一段譯文", kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT, evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION)
    assert previous.evidence[0].evidence_type == csm.EvidenceType.TRANSLATION_OBSERVATION
    with pytest.raises(csm.ContextSceneValidationError):
        context("不是譯文證據", kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT)
    with pytest.raises(csm.ContextSceneValidationError):
        context("長" * 513, kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT, evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION)


def test_duplicate_merges_but_multivalued_context_does_not_conflict():
    store = csm.ContextMemoryStore()
    one = context("相同內容", segment="seg-1")
    two = context("相同內容", segment="seg-2")
    assert csm.add_or_merge_context(store, one, now=T0).disposition == csm.AddDisposition.ACCEPTED
    assert csm.add_or_merge_context(store, two, now=T1).disposition == csm.AddDisposition.MERGED
    assert len(store.contexts) == 1 and len(store.get_context(one.context_id).evidence) == 2
    csm.add_or_merge_context(store, context("另一則", segment="seg-3"), now=T1)
    assert len(store.contexts) == 2 and not store.conflicts


def test_same_tier_singular_conflict_is_visible_and_excluded():
    store = csm.ContextMemoryStore()
    one = context("室內", kind=csm.ContextType.LOCATION_STATE, segment="a")
    two = context("室外", kind=csm.ContextType.LOCATION_STATE, segment="b")
    csm.add_or_merge_context(store, one, now=T0)
    result = csm.add_or_merge_context(store, two, now=T1)
    assert result.disposition == csm.AddDisposition.CONFLICT and store.conflicts
    selected = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, now=T2)
    assert not selected.selected_records
    assert all(selected.drop_reasons[item] == ("conflict",) for item in result.conflicting_ids)


def test_source_beats_translation_and_human_approved_beats_source():
    store = csm.ContextMemoryStore()
    translated = context("譯文位置", kind=csm.ContextType.LOCATION_STATE, evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION, segment="t")
    observed = context("原文位置", kind=csm.ContextType.LOCATION_STATE, segment="s")
    csm.add_or_merge_context(store, translated, now=T0)
    assert csm.add_or_merge_context(store, observed, now=T1).disposition == csm.AddDisposition.SUPERSEDED
    human = context("人工核准位置", kind=csm.ContextType.LOCATION_STATE, evidence_kind=csm.EvidenceType.HUMAN_APPROVED, segment="h", approval=csm.ApprovalStatus.APPROVED)
    assert csm.add_or_merge_context(store, human, now=T2).disposition == csm.AddDisposition.SUPERSEDED
    result = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, now=T2)
    assert [item.value for item in result.selected_records] == ["人工核准位置"]


def test_inference_and_historical_import_are_not_approved_facts():
    store = csm.ContextMemoryStore()
    inferred = context("推測", evidence_kind=csm.EvidenceType.AI_INFERENCE, segment="i", confidence=.99, experimental=True)
    historical = context("歷史匯入", evidence_kind=csm.EvidenceType.HISTORICAL_IMPORT, segment="h")
    csm.add_or_merge_context(store, inferred, now=T0)
    csm.add_or_merge_context(store, historical, now=T0)
    selected = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, now=T1)
    assert inferred.approval_status == csm.ApprovalStatus.PENDING
    assert inferred.context_id in selected.dropped_records
    assert [item.value for item in selected.selected_records] == ["歷史匯入"]


def test_scene_participant_states_are_distinct_and_exit_is_explicit():
    store = scene()
    for index, status in enumerate(("present", "mentioned", "absent", "unknown")):
        csm.add_scene_participant(store, "scene-1", character_id=f"char-{index}", participant_status=status, presence_confidence=.9, evidence_reference=f"ev-{index}", updated_at=T1)
    csm.remove_scene_participant(store, "scene-1", character_id="char-0", updated_at=T2)
    statuses = {item.character_id: item.participant_status.value for item in store.get_scene("scene-1").participants}
    assert statuses == {"char-0": "exited_scene", "char-1": "mentioned", "char-2": "absent", "char-3": "unknown"}


def test_same_unknown_and_real_scene_transitions_are_conservative():
    store = scene()
    csm.add_scene_participant(store, "scene-1", character_id="char-1", participant_status="present", presence_confidence=.9, evidence_reference="ev", updated_at=T1)
    temporary = context("暫時位置", kind=csm.ContextType.LOCATION_STATE)
    csm.add_or_merge_context(store, temporary, now=T0)
    before = store.snapshot()
    assert not csm.transition_scene(store, from_scene_id="scene-1", boundary="same_scene")["changed"]
    assert not csm.transition_scene(store, from_scene_id="scene-1", boundary="unknown_transition")["changed"]
    assert store.snapshot() == before
    result = csm.transition_scene(store, from_scene_id="scene-1", boundary="scene_transition", to_scene_id="scene-2", evidence=evidence(), transitioned_at=T2)
    assert temporary.context_id in result["expired_context_ids"]
    assert store.get_scene("scene-1").participants[0].participant_status == csm.ParticipantStatus.EXITED_SCENE
    assert not store.get_scene("scene-2").participants


def test_chapter_transition_expires_chapter_scoped_context_only():
    store = scene()
    record = context("章摘要", kind=csm.ContextType.SCENE_SUMMARY, scene=None, expiry=csm.ExpiryPolicy(csm.ExpiryKind.CHAPTER_SCOPE, "chapter-1"))
    stable = context("穩定關係", kind=csm.ContextType.RELATIONSHIP_STATE, scene=None, expiry=csm.ExpiryPolicy(csm.ExpiryKind.NEVER), segment="stable")
    csm.add_or_merge_context(store, record, now=T0); csm.add_or_merge_context(store, stable, now=T0)
    csm.transition_chapter(store, from_scene_id="scene-1", to_scene_id="scene-2", to_chapter_id="chapter-2", evidence=evidence(), transitioned_at=T2)
    assert store.get_context(record.context_id).status == csm.RecordStatus.EXPIRED
    assert store.get_context(stable.context_id).status == csm.RecordStatus.ACTIVE


def test_unresolved_reference_never_auto_resolves_and_human_resolution_is_evidenced():
    store = scene()
    ref = csm.create_unresolved_reference(surface_form="他", reference_type="person", candidate_targets=("char-a", "char-b"), evidence=evidence(), confidence=.99, scope="scene-1", expiry=csm.ExpiryPolicy(csm.ExpiryKind.SCENE_SCOPE, "scene-1"))
    csm.add_unresolved_reference(store, "scene-1", ref, updated_at=T1)
    assert store.get_scene("scene-1").unresolved_references[0].resolution_status == csm.ResolutionStatus.UNRESOLVED
    with pytest.raises(csm.ContextSceneValidationError):
        csm.resolve_reference(store, "scene-1", reference_id=ref.reference_id, target="char-a", updated_at=T2)
    approved = evidence(csm.EvidenceType.HUMAN_APPROVED, segment="approval")
    csm.resolve_reference(store, "scene-1", reference_id=ref.reference_id, target="char-a", human_approved=True, approval_evidence=approved, updated_at=T2)
    resolved = store.get_scene("scene-1").unresolved_references[0]
    assert resolved.resolution_status == csm.ResolutionStatus.HUMAN_APPROVED and resolved.resolved_target == "char-a"


def test_previous_translation_stale_hash_sequence_scope_and_duplicate_suppression():
    store = csm.ContextMemoryStore()
    prior = context("短譯文", kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT, evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION, sequence=4)
    csm.add_or_merge_context(store, prior, now=T0)
    wrong_hash = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=5, expected_previous_translation_hash=sha("wrong"), now=T1)
    assert wrong_hash.drop_reasons[prior.context_id] == ("stale",)
    right_hash = prior.evidence[0].translation_text_hash
    selected = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=5, expected_previous_translation_hash=right_hash, now=T1)
    assert len(selected.selected_records) == 1
    duplicate = context("短譯文", kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT, evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION, segment="dup", sequence=4)
    assert csm.add_or_merge_context(store, duplicate, now=T1).disposition == csm.AddDisposition.MERGED


def test_token_budgets_and_fingerprint_are_deterministic_and_separate():
    store = csm.ContextMemoryStore()
    for index in range(30):
        csm.add_or_merge_context(store, context(f"內容 {index} " * 5, segment=f"s-{index}"), now=T0)
    zero = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, token_budget=0, now=T1)
    one = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, token_budget=64, now=T1)
    two = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=2, token_budget=64, now=T1)
    assert not zero.selected_records and one.estimated_tokens <= 64 and one == two
    with pytest.raises(csm.ContextSceneValidationError):
        csm.select_context_for_translation(store, token_budget=-1)


def test_lifecycle_rollback_and_scene_rollback_preserve_history():
    store = scene()
    record = context("可回退內容")
    csm.add_or_merge_context(store, record, now=T0)
    csm.expire_context(store, record.context_id, expired_at=T1)
    restored = csm.rollback_context(store, record.context_id, rolled_back_at=T2)
    assert restored.status == csm.RecordStatus.ACTIVE and restored.version == 3
    csm.add_scene_participant(store, "scene-1", character_id="char-1", participant_status="present", presence_confidence=.9, evidence_reference="ev", updated_at=T1)
    csm.remove_scene_participant(store, "scene-1", character_id="char-1", updated_at=T2)
    rolled_scene = csm.rollback_scene(store, "scene-1", target_version=2, rolled_back_at="2026-07-16T00:03:00Z")
    assert rolled_scene.participants[0].participant_status == csm.ParticipantStatus.PRESENT


def test_invalid_rollback_does_not_mutate_store():
    store = csm.ContextMemoryStore(); record = context(); csm.add_or_merge_context(store, record, now=T0)
    before = csm.serialize_context_store(store)
    with pytest.raises(csm.ContextSceneValidationError):
        csm.rollback_context(store, record.context_id, target_version=99, rolled_back_at=T1)
    assert csm.serialize_context_store(store) == before


def test_serialization_round_trip_canonical_and_fail_closed():
    store = scene(); csm.add_or_merge_context(store, context(), now=T0)
    encoded = csm.serialize_context_store(store)
    assert csm.serialize_context_store(csm.deserialize_context_store(encoded)) == encoded
    data = json.loads(encoded); data["schema_version"] = "2.0"
    with pytest.raises(csm.ContextSceneValidationError): csm.deserialize_context_store(json.dumps(data))
    for malformed in ("{", "[]", "not json"):
        with pytest.raises(csm.ContextSceneValidationError): csm.deserialize_context_store(malformed)


def test_invalid_enum_timestamp_confidence_path_and_secret_fail_closed():
    store = csm.ContextMemoryStore(); record = context(); csm.add_or_merge_context(store, record, now=T0)
    base = json.loads(csm.serialize_context_store(store))
    for field, value in (("confidence", 2), ("status", "unknown"), ("created_at", "yesterday"), ("context_id", "../escape")):
        data = json.loads(json.dumps(base)); data["contexts"][0][field] = value
        with pytest.raises((csm.ContextSceneValidationError, ValueError)): csm.deserialize_context_store(json.dumps(data))
    with pytest.raises(csm.ContextSceneValidationError):
        context("Bear" + "er populated-token-value-123456789", segment="secret")


def test_public_api_is_finite_and_has_no_runtime_or_prompt_entrypoint():
    assert "select_context_for_translation" in csm.__all__
    assert "serialize_context_store" in csm.__all__
    # Persistence API added in Batch 3D-2
    assert "compute_book_identity" in csm.__all__
    assert "get_context_memory_file_path" in csm.__all__
    assert "save_context_memory" in csm.__all__
    assert "load_context_memory" in csm.__all__
    assert "verify_context_memory_integrity" in csm.__all__
    assert "load_or_create_context_memory" in csm.__all__
    assert not {"run_provider", "build_prompt", "translate", "execute_runtime"} & set(csm.__all__)
    assert len(csm.__all__) < 80
