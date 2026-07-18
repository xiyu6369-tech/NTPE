from __future__ import annotations

import hashlib
from pathlib import Path

import core.character_memory_v2 as cm
import core.context_scene_memory as cs
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package


T0 = "2026-07-19T00:00:00Z"
T1 = "2026-07-19T00:01:00Z"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _character_store() -> cm.MemoryStore:
    store = cm.MemoryStore()
    evidence = cm.create_evidence(
        evidence_type="human_approved",
        source_case_id="runtime-memory",
        source_segment_id="name",
        source_text_hash=_sha("영희"),
        excerpt="영희",
        language="ko",
        observed_at=T0,
    )
    record = cm.create_memory(
        character_id="char-yeonghui",
        fact_type="canonical_name",
        value="英熙",
        evidence=evidence,
        confidence=0.9,
        approval_status="approved",
        approval_metadata=cm.ApprovalMetadata("英熙", T0, "reviewer", "decision"),
        created_at=T0,
    )
    cm.add_or_merge_memory(store, record, now=T0)
    return store


def _context_store() -> cs.ContextMemoryStore:
    store = cs.ContextMemoryStore()
    evidence = cs.create_context_evidence(
        evidence_type="source_observation",
        source_case_id="runtime-memory",
        source_segment_id="scene",
        source_text_hash=_sha("서재"),
        excerpt="서재",
        language="ko",
        observed_at=T0,
    )
    scene = cs.create_scene_memory(scene_id="scene-1", chapter_id="chapter-1", location="書房", evidence=evidence, created_at=T0)
    cs.add_scene(store, scene)
    cs.add_scene_participant(
        store,
        "scene-1",
        character_id="char-yeonghui",
        participant_status="present",
        presence_confidence=0.95,
        evidence_reference="scene-evidence",
        updated_at=T1,
    )
    context = cs.create_context_memory(
        context_type="speaker_state",
        value="英熙正在說話",
        evidence=evidence,
        confidence=0.95,
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=1,
        created_at=T0,
    )
    cs.add_or_merge_context(store, context, now=T0)
    continuity = cs.create_context_memory(
        context_type="source_context_excerpt",
        value="上一段仍在書房",
        evidence=evidence,
        confidence=0.95,
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=1,
        created_at=T0,
    )
    cs.add_or_merge_context(store, continuity, now=T0)
    return store


def _build(**quality):
    options = TxtTranslationOptions(input_path=Path("novel.txt"), output_dir=Path("output"), **quality)
    return build_prompt_package(
        options=options,
        chunk_text="영희가 말했다.",
        chunk_index=2,
        chunk_total=3,
        locked_dictionary={"영희": "英熙"},
        previous_context="그녀는 서재에 있었다.",
    )


def test_character_only_runtime_injection_uses_read_only_frozen_store() -> None:
    store = _character_store()
    before = cm.serialize_memory_store(store)
    package = _build(
        quality_character_memory_v72=True,
        quality_character_store_v72=store,
        quality_active_character_ids_v72=("char-yeonghui",),
        quality_selection_time_v72=T1,
    )
    prompt = package["prompt"]["user_prompt"]
    assert "人物一致性記憶" in prompt and "英熙" in prompt
    assert "目前場景提示" not in prompt and "自然度政策" not in prompt
    assert cm.serialize_memory_store(store) == before


def test_context_scene_only_runtime_injection_uses_read_only_frozen_store() -> None:
    store = _context_store()
    before = cs.serialize_context_store(store)
    package = _build(
        quality_context_scene_v72=True,
        quality_context_scene_store_v72=store,
        quality_active_character_ids_v72=("char-yeonghui",),
        quality_chapter_id_v72="chapter-1",
        quality_scene_id_v72="scene-1",
        quality_selection_time_v72="2026-07-19T00:02:00Z",
    )
    prompt = package["prompt"]["user_prompt"]
    assert "目前場景提示" in prompt and "英熙正在說話" in prompt
    assert "人物一致性記憶" not in prompt and "自然度政策" not in prompt
    assert cs.serialize_context_store(store) == before


def test_all_enabled_runtime_fingerprint_and_prompt_are_deterministic() -> None:
    characters = _character_store()
    context = _context_store()
    kwargs = dict(
        quality_integration_v72=True,
        quality_character_store_v72=characters,
        quality_context_scene_store_v72=context,
        quality_active_character_ids_v72=("char-yeonghui",),
        quality_chapter_id_v72="chapter-1",
        quality_scene_id_v72="scene-1",
        quality_selection_time_v72="2026-07-19T00:02:00Z",
    )
    one, two = _build(**kwargs), _build(**kwargs)
    one_meta = one["prompt_runtime"]["translation_quality_integration_v72"]
    two_meta = two["prompt_runtime"]["translation_quality_integration_v72"]
    assert one["prompt"]["user_prompt"] == two["prompt"]["user_prompt"]
    assert one_meta["selection_fingerprint"] == two_meta["selection_fingerprint"]
    assert one_meta["character_records_selected"] >= 1
    assert one_meta["context_records_selected"] >= 1 and one_meta["scene_records_selected"] >= 1
