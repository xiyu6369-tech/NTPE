from __future__ import annotations

import hashlib
import json
import time

import pytest

import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module
from core.character_memory_v2 import (
    ApprovalMetadata, ApprovalStatus, EvidenceType, ExpiryKind, ExpiryPolicy,
    FactType, MemoryStore, add_or_merge_memory, create_evidence, create_memory,
)


T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"
ENABLED = {
    "LCR_SHADOW_ENABLED": True,
    "LCR_KILL_SWITCH": False,
    "LCR_CHARACTER_MEMORY_SHADOW": True,
}


def package(language: str = "ja") -> dict[str, object]:
    return {
        "package_id": "fixture-1",
        "project": {"source_language": language, "target_language": "zh-Hant"},
        "session": {"session_id": "fixture", "chunk_index": 1, "resume_key": "fixture:1"},
        "source": {"source_hash": "a" * 40, "chunk_text": "must-not-enter-snapshot"},
        "prompt": {"system_prompt": "must-not-change"},
        "model_profile": {"engine": "baseline", "model": "baseline-model"},
        "runtime": {"version": "fixture"},
        "raw_provider_request": "must-not-enter-snapshot",
    }


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def record(index: int, value: str, *, kind: EvidenceType = EvidenceType.SOURCE_OBSERVATION,
           fact_type: FactType = FactType.OTHER, approved: bool = False,
           expiry: ExpiryPolicy | None = None, language: str = "ja"):
    evidence = create_evidence(
        evidence_type=EvidenceType.HUMAN_APPROVED if approved else kind,
        source_case_id=f"case-{index}", source_segment_id=f"seg-{index}",
        source_text_hash=_sha(value), excerpt=value, language=language, observed_at=T0,
    )
    return create_memory(
        character_id="char-1", fact_type=fact_type, value=value, evidence=evidence,
        confidence=0.99, created_at=T0, expiry_policy=expiry,
        approval_status=ApprovalStatus.APPROVED if approved else ApprovalStatus.PENDING,
        approval_metadata=ApprovalMetadata(value, T0, "human", f"decision-{index}") if approved else None,
    )


def store_with_selection_cases() -> MemoryStore:
    store = MemoryStore()
    rows = (
        record(1, "承認済み名", fact_type=FactType.CANONICAL_NAME, approved=True),
        record(2, "兄弟関係", fact_type=FactType.RELATIONSHIP),
        record(3, "推測された性格", kind=EvidenceType.AI_INFERENCE, fact_type=FactType.PERSONALITY_TRAIT),
        record(4, "期限切れ", fact_type=FactType.TEMPORAL_STATE,
               expiry=ExpiryPolicy(ExpiryKind.TIMESTAMP, expires_at="2026-07-16T00:00:30Z")),
    )
    for item in rows:
        add_or_merge_memory(store, item, now=T0)
    add_or_merge_memory(store, record(5, "敵対", fact_type=FactType.RELATIONSHIP), now=T0)
    return store


def snapshot(store: MemoryStore, *, budget: int = 128, language: str = "ja", ids=("char-1",)):
    return lcr.build_character_memory_shadow_input(
        store, document_id="doc-1", chunk_index=1, source_language=language,
        target_language="zh-Hant", character_ids=ids, snapshot_id="snapshot-1",
        token_budget=budget, created_at=T1,
    )


def test_flag_priority_and_default_off_fail_closed():
    assert not lcr.resolve_hook_flags({"LCR_SHADOW_ENABLED": True, "LCR_KILL_SWITCH": False})[lcr.CHARACTER_MEMORY_FLAG]
    assert not lcr.resolve_hook_flags({**ENABLED, "LCR_KILL_SWITCH": True})[lcr.CHARACTER_MEMORY_FLAG]
    assert not lcr.resolve_hook_flags({**ENABLED, "LCR_CHARACTER_MEMORY_SHADOW": "unknown"})[lcr.CHARACTER_MEMORY_FLAG]


def test_valid_selection_is_redacted_bounded_read_only_and_deterministic():
    store = store_with_selection_cases()
    before = json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True)
    item = snapshot(store)
    first = lcr.evaluate_character_memory_shadow(item, now=T1)
    second = lcr.evaluate_character_memory_shadow(item, now=T1)
    assert first.selected_memory_ids == second.selected_memory_ids
    assert first.selected_fingerprint == second.selected_fingerprint
    assert first.estimated_tokens <= 128
    assert first.memory_injected is first.prompt_identity_changed is first.production_output_changed is False
    assert first.cache_identity_impact_planned and not first.cache_identity_applied
    assert first.inference_excluded_count == 1 and first.conflict_count == 2 and first.expired_count == 1
    assert "推測された性格" not in repr(first)
    assert json.dumps(store.to_dict(), ensure_ascii=False, sort_keys=True) == before


def test_empty_metadata_budget_and_unknown_profile_fail_safe():
    store = store_with_selection_cases()
    assert lcr.evaluate_character_memory_shadow(snapshot(store, ids=()), now=T1).status == "no_eligible_memory"
    zero = lcr.evaluate_character_memory_shadow(snapshot(store, budget=0), now=T1)
    assert zero.selected_count == 0 and zero.estimated_tokens == 0
    assert lcr.evaluate_character_memory_shadow(snapshot(store, language="xx"), now=T1).status == "invalid"
    with pytest.raises(ValueError):
        snapshot(store, budget=-1)
    with pytest.raises(ValueError):
        lcr.build_character_memory_shadow_input(store, document_id="../escape", chunk_index=0,
            source_language="ja", target_language="zh-Hant", character_ids=(), snapshot_id="snap")


def test_hook_metadata_unavailable_and_full_integration_preserve_all_identities():
    missing = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED)
    assert missing.status == "completed" and missing.evidence
    assert missing.evidence.character_memory.status == "metadata_unavailable"
    store = store_with_selection_cases()
    before = json.dumps(package(), sort_keys=True)
    item = package()
    result = lcr.run_read_only_lcr_shadow_hook(
        item, feature_flags=ENABLED, character_memory_store=store,
        character_ids=("char-1",), character_memory_snapshot_id="snapshot-1",
        created_at_factory=lambda: T1,
    )
    assert result.evidence and result.evidence.character_memory
    assert result.evidence.character_memory.module == "character_memory"
    assert result.evidence.modules_evaluated.count("character_memory") == 1
    assert result.before_hash == result.after_hash
    assert result.prompt_before_hash == result.prompt_after_hash
    assert result.provider_identity_before == result.provider_identity_after
    assert result.resume_before_hash == result.resume_after_hash
    assert result.output_contract_before_hash == result.output_contract_after_hash
    assert json.dumps(item, sort_keys=True) == before


def test_selected_fingerprint_ignores_unselected_inference_but_tracks_selected_change():
    base = MemoryStore()
    add_or_merge_memory(base, record(1, "承認名", approved=True, fact_type=FactType.CANONICAL_NAME), now=T0)
    first = lcr.evaluate_character_memory_shadow(snapshot(base), now=T1)
    inferred = MemoryStore.from_dict(base.to_dict())
    add_or_merge_memory(inferred, record(2, "推論", kind=EvidenceType.AI_INFERENCE), now=T0)
    second = lcr.evaluate_character_memory_shadow(snapshot(inferred), now=T1)
    changed = MemoryStore()
    add_or_merge_memory(changed, record(3, "別の承認名", approved=True, fact_type=FactType.CANONICAL_NAME), now=T0)
    third = lcr.evaluate_character_memory_shadow(snapshot(changed), now=T1)
    assert first.selected_fingerprint == second.selected_fingerprint
    assert first.selected_fingerprint != third.selected_fingerprint


def test_character_selector_timeout_uses_existing_worker_and_discards_late_result(monkeypatch):
    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.evaluate_character_memory_shadow

    def slow(*args, **kwargs):
        time.sleep(0.2)
        return original(*args, **kwargs)

    monkeypatch.setattr(hook_module, "evaluate_character_memory_shadow", slow)
    sink = lcr.InMemoryEvidenceSink()
    before_store = json.dumps(store_with_selection_cases().to_dict(), sort_keys=True)
    store = store_with_selection_cases()
    started = time.perf_counter()
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED,
        character_memory_store=store, character_ids=("char-1",),
        character_memory_snapshot_id="snapshot-1", created_at_factory=lambda: T1,
        evidence_sink=sink)
    assert (time.perf_counter() - started) * 1000 < 50
    assert result.status == "timed_out" and result.result_discarded
    assert sink.records == []
    assert lcr.wait_for_shadow_idle(1.0) and sink.records == []
    assert json.dumps(store.to_dict(), sort_keys=True) == before_store
    stats = lcr.executor_snapshot()
    assert stats.worker_count == 1 and stats.queue_capacity == 1 and stats.queue_depth == 0


def test_activation_gate_never_authorizes_active_integration():
    keys = (
        "single_production_hook_unchanged", "character_memory_flag_default_false",
        "kill_switch_default_true", "immutable_snapshot_verified", "selection_read_only",
        "store_hash_unchanged", "prompt_identity_unchanged", "provider_identity_unchanged",
        "resume_unchanged", "output_unchanged", "memory_injected_false",
        "provider_requests_zero", "network_requests_zero", "bounded_deadline_pass",
        "late_results_discarded", "worker_count_bounded", "queue_bounded", "security_pass",
        "all_regressions_pass", "manual_approval_present",
    )
    ready = lcr.evaluate_character_memory_shadow_gate({key: True for key in keys})
    assert ready.status == "ready_for_context_scene_shadow" and not ready.active_production_authorized
    assert lcr.evaluate_character_memory_shadow_gate({key: True for key in keys if key != "memory_injected_false"}).status == "insufficient_evidence"
    evidence = {key: True for key in keys}
    evidence["memory_injected_false"] = False
    assert lcr.evaluate_character_memory_shadow_gate(evidence).status == "not_ready"
