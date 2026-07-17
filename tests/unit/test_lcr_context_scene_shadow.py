from __future__ import annotations

import json
import time

import pytest

import core.context_scene_memory as csm
import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module
from tests.unit.test_context_scene_memory import T0, T1, T2, context, evidence, scene, sha
from tests.unit.test_lcr_character_memory_shadow import package as base_package
from tests.unit.test_lcr_character_memory_shadow import store_with_selection_cases


ENABLED = {
    "LCR_SHADOW_ENABLED": True,
    "LCR_KILL_SWITCH": False,
    "LCR_CONTEXT_SCENE_SHADOW": True,
}


def package(language: str = "ko") -> dict[str, object]:
    value = base_package(language)
    value["project"]["target_language"] = "zh-Hant"
    return value


def context_store() -> tuple[csm.ContextMemoryStore, str]:
    store = scene()
    csm.update_scene_state(store, "scene-1", location="密室", time_state="深夜",
                           active_speaker="char-present", point_of_view="char-present",
                           evidence=evidence(segment="scene-state"), updated_at=T1)
    csm.add_scene_participant(store, "scene-1", character_id="char-present", participant_status="present",
                              presence_confidence=.99, evidence_reference="source-evidence", updated_at=T1)
    csm.add_scene_participant(store, "scene-1", character_id="char-mentioned", participant_status="mentioned",
                              presence_confidence=.9, evidence_reference="source-evidence-2", updated_at=T1)
    csm.add_scene_participant(store, "scene-1", character_id="char-exited", participant_status="present",
                              presence_confidence=.9, evidence_reference="source-evidence-3", updated_at=T1)
    csm.remove_scene_participant(store, "scene-1", character_id="char-exited", updated_at=T2)
    ref = csm.create_unresolved_reference(
        surface_form="敏感指涉文字", reference_type="person",
        candidate_targets=("char-present", "char-mentioned"), evidence=evidence(segment="ref"),
        confidence=.99, scope="scene-1", expiry=csm.ExpiryPolicy(csm.ExpiryKind.SCENE_SCOPE, "scene-1"),
    )
    csm.add_unresolved_reference(store, "scene-1", ref, updated_at=T2)
    csm.add_or_merge_context(store, context("有效來源情境", segment="valid", sequence=4), now=T0)
    csm.add_or_merge_context(store, context("推論不得選入", evidence_kind=csm.EvidenceType.AI_INFERENCE,
                                             segment="inference", sequence=4, experimental=True), now=T0)
    prior = context("完整上一段譯文不得保留", kind=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT,
                    evidence_kind=csm.EvidenceType.TRANSLATION_OBSERVATION, segment="previous", sequence=4)
    csm.add_or_merge_context(store, prior, now=T0)
    csm.add_or_merge_context(store, context("過期狀態", segment="expired", sequence=4,
        expiry=csm.ExpiryPolicy(csm.ExpiryKind.TIMESTAMP, expires_at="2026-07-16T00:00:30Z")), now=T0)
    csm.add_or_merge_context(store, context("位置甲", kind=csm.ContextType.LOCATION_STATE, segment="conflict-a", sequence=4), now=T0)
    csm.add_or_merge_context(store, context("位置乙", kind=csm.ContextType.LOCATION_STATE, segment="conflict-b", sequence=4), now=T0)
    return store, prior.evidence[0].translation_text_hash or ""


def snapshot(store: csm.ContextMemoryStore, previous_hash: str, *, budget: int = 256,
             language: str = "ko", character_fingerprint: str = "character-fp"):
    return lcr.build_context_scene_shadow_input(
        store, document_id="doc-1", chunk_index=1, source_language=language,
        target_language="zh-Hant", chapter_id="chapter-1", scene_id="scene-1",
        sequence_index=5, character_ids=("char-present", "char-mentioned", "char-exited"),
        snapshot_id="context-snapshot-1", token_budget=budget,
        previous_translation_allowed=True, expected_previous_translation_hash=previous_hash,
        character_memory_selection_fingerprint=character_fingerprint, created_at=T2,
    )


def test_flag_priority_default_off_and_character_flag_independence():
    assert not lcr.resolve_hook_flags({"LCR_SHADOW_ENABLED": True, "LCR_KILL_SWITCH": False})[lcr.CONTEXT_SCENE_FLAG]
    assert not lcr.resolve_hook_flags({**ENABLED, "LCR_KILL_SWITCH": True})[lcr.CONTEXT_SCENE_FLAG]
    assert not lcr.resolve_hook_flags({**ENABLED, "LCR_CONTEXT_SCENE_SHADOW": "unknown"})[lcr.CONTEXT_SCENE_FLAG]
    flags = lcr.resolve_hook_flags({**ENABLED, "LCR_CHARACTER_MEMORY_SHADOW": False})
    assert flags[lcr.CONTEXT_SCENE_FLAG] and not flags[lcr.CHARACTER_MEMORY_FLAG]


def test_snapshot_is_detached_redacted_and_rejects_invalid_inputs():
    store, previous_hash = context_store()
    before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    item = snapshot(store, previous_hash)
    assert "完整上一段譯文不得保留" not in repr(item)
    assert "敏感指涉文字" not in repr(item)
    assert "[redacted]" in repr(item)
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == before
    with pytest.raises(ValueError):
        snapshot(store, previous_hash, budget=-1)
    with pytest.raises(ValueError):
        lcr.build_context_scene_shadow_input(store, document_id="../escape", chunk_index=0,
            source_language="ko", target_language="zh-Hant", chapter_id="c", scene_id="s",
            sequence_index=0, snapshot_id="snap")


def test_valid_scene_selection_is_bounded_read_only_and_preserves_unresolved():
    store, previous_hash = context_store()
    before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    result = lcr.evaluate_context_scene_shadow(snapshot(store, previous_hash), now=T2)
    assert result.status in {"selected", "budget_limited"}
    assert result.estimated_tokens <= 256 and result.budget == 256
    assert "char-present" in result.present_character_ids
    assert "char-mentioned" in result.mentioned_character_ids
    assert "char-exited" in result.exited_character_ids
    assert result.unresolved_reference_count == 1
    assert result.previous_translation_candidate and result.previous_translation_selected
    assert result.inference_excluded == 1 and result.expired_excluded >= 1 and result.conflict_excluded == 2
    assert not result.context_injected and not result.previous_translation_injected
    assert not result.scene_state_applied and not result.cache_identity_applied
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == before


def test_previous_translation_stale_budget_and_profile_fail_closed():
    store, previous_hash = context_store()
    stale = lcr.evaluate_context_scene_shadow(snapshot(store, sha("wrong")), now=T2)
    assert stale.stale_excluded >= 1 and not stale.previous_translation_selected
    zero = lcr.evaluate_context_scene_shadow(snapshot(store, previous_hash, budget=0), now=T2)
    assert zero.selected_records == 0 and zero.estimated_tokens == 0
    with pytest.raises(ValueError):
        snapshot(store, previous_hash, language="xx")


def test_fingerprints_are_deterministic_and_combined_tracks_character_only():
    store, previous_hash = context_store()
    first = lcr.evaluate_context_scene_shadow(snapshot(store, previous_hash, character_fingerprint="a"), now=T2)
    second = lcr.evaluate_context_scene_shadow(snapshot(store, previous_hash, character_fingerprint="a"), now=T2)
    third = lcr.evaluate_context_scene_shadow(snapshot(store, previous_hash, character_fingerprint="b"), now=T2)
    assert first.selected_fingerprint == second.selected_fingerprint == third.selected_fingerprint
    assert first.combined_context_fingerprint == second.combined_context_fingerprint
    assert first.combined_context_fingerprint != third.combined_context_fingerprint


def test_character_memory_interoperability_is_one_way_and_budget_separate():
    store, previous_hash = context_store()
    character_store = store_with_selection_cases()
    context_before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    character_before = json.dumps(character_store.to_dict(), ensure_ascii=False, sort_keys=True)
    flags = {**ENABLED, "LCR_CHARACTER_MEMORY_SHADOW": True}
    result = lcr.run_read_only_lcr_shadow_hook(
        package(), feature_flags=flags, context_scene_store=store,
        context_scene_snapshot_id="context-combined", chapter_id="chapter-1", scene_id="scene-1",
        sequence_index=5, character_memory_store=character_store, character_ids=("char-1",),
        character_memory_snapshot_id="character-combined", previous_translation_allowed=True,
        expected_previous_translation_hash=previous_hash, created_at_factory=lambda: T2,
    )
    assert result.evidence and result.evidence.character_memory and result.evidence.context_scene
    assert result.evidence.character_memory.token_budget == 128
    assert result.evidence.context_scene.budget == 256
    assert result.evidence.character_memory.estimated_tokens + result.evidence.context_scene.estimated_tokens <= 384
    assert result.evidence.context_scene.combined_context_fingerprint
    assert result.evidence.context_scene.combined_context_fingerprint != result.evidence.context_scene.selected_fingerprint
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == context_before
    assert json.dumps(character_store.to_dict(), ensure_ascii=False, sort_keys=True) == character_before


def test_hook_metadata_unavailable_and_integration_preserve_identities():
    missing = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED)
    assert missing.evidence and missing.evidence.context_scene.status == "metadata_unavailable"
    store, previous_hash = context_store()
    production = package()
    before = json.dumps(production, ensure_ascii=False, sort_keys=True)
    result = lcr.run_read_only_lcr_shadow_hook(
        production, feature_flags=ENABLED, context_scene_store=store,
        context_scene_snapshot_id="snapshot-hook", chapter_id="chapter-1", scene_id="scene-1",
        sequence_index=5, character_ids=("char-present",), previous_translation_allowed=True,
        expected_previous_translation_hash=previous_hash, created_at_factory=lambda: T2,
    )
    assert result.evidence and result.evidence.context_scene
    assert result.evidence.modules_evaluated.count("context_scene") == 1
    assert result.before_hash == result.after_hash
    assert result.prompt_before_hash == result.prompt_after_hash
    assert result.provider_identity_before == result.provider_identity_after
    assert result.resume_before_hash == result.resume_after_hash
    assert result.output_contract_before_hash == result.output_contract_after_hash
    assert result.evidence.provider_requests_executed == 0
    assert json.dumps(production, ensure_ascii=False, sort_keys=True) == before


def test_timeout_discards_late_context_result_and_never_writes_sink(monkeypatch):
    assert lcr.wait_for_shadow_idle(1.0)
    store, previous_hash = context_store()
    original = hook_module.evaluate_context_scene_shadow
    def slow(*args, **kwargs):
        time.sleep(.2)
        return original(*args, **kwargs)
    monkeypatch.setattr(hook_module, "evaluate_context_scene_shadow", slow)
    sink = lcr.InMemoryEvidenceSink()
    before = json.dumps(store.to_dict(), sort_keys=True)
    started = time.perf_counter()
    result = lcr.run_read_only_lcr_shadow_hook(
        package(), feature_flags=ENABLED, evidence_sink=sink, context_scene_store=store,
        context_scene_snapshot_id="snapshot-timeout", chapter_id="chapter-1", scene_id="scene-1",
        sequence_index=5, previous_translation_allowed=True,
        expected_previous_translation_hash=previous_hash, created_at_factory=lambda: T2,
    )
    assert (time.perf_counter() - started) * 1000 < 50
    assert result.status == "timed_out" and result.result_discarded
    assert lcr.wait_for_shadow_idle(1.0) and sink.records == []
    assert json.dumps(store.to_dict(), sort_keys=True) == before
    stats = lcr.executor_snapshot()
    assert stats.worker_count == 1 and stats.queue_capacity == 1 and stats.queue_depth == 0


def test_activation_gate_stops_at_dual_pass_shadow_readiness():
    keys = (
        "single_production_hook_unchanged", "production_wrapper_unchanged",
        "context_scene_flag_default_false", "kill_switch_default_true", "immutable_snapshot_verified",
        "context_store_unchanged", "character_store_unchanged", "prompt_identity_unchanged",
        "provider_identity_unchanged", "resume_unchanged", "output_unchanged", "context_injected_false",
        "previous_translation_injected_false", "scene_state_applied_false", "cache_identity_applied_false",
        "provider_requests_zero", "network_requests_zero", "deadline_isolation_pass",
        "late_result_writes_zero", "worker_bounded", "queue_bounded", "security_pass",
        "all_regressions_pass", "manual_approval_present",
    )
    ready = lcr.evaluate_context_scene_shadow_gate({key: True for key in keys})
    assert ready.status == "ready_for_dual_pass_shadow" and not ready.active_production_authorized
    evidence_map = {key: True for key in keys}
    evidence_map["context_injected_false"] = False
    assert lcr.evaluate_context_scene_shadow_gate(evidence_map).status == "not_ready"
    assert lcr.evaluate_context_scene_shadow_gate({key: True for key in keys[:-1]}).status == "insufficient_evidence"
