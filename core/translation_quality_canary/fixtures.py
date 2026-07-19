from __future__ import annotations

import hashlib

import core.character_memory_v2 as cm
import core.context_scene_memory as cs


FIXED_TIME = "2026-07-19T00:00:00Z"
SELECTION_TIME = "2026-07-19T00:03:00Z"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_offline_canary_stores() -> tuple[cm.MemoryStore, cs.ContextMemoryStore]:
    """Build deterministic, synthetic, read-only engineering fixtures."""
    characters = cm.MemoryStore()
    character_evidence = cm.create_evidence(
        evidence_type=cm.EvidenceType.HUMAN_APPROVED,
        source_case_id="te-v72-stage1251-engineering-fixture",
        source_segment_id="character-name",
        source_text_hash=_sha("character-name"),
        excerpt="fixture-name",
        language="ko",
        observed_at=FIXED_TIME,
    )
    character = cm.create_memory(
        character_id="char-yeonghui",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="Yeong-hui",
        evidence=character_evidence,
        confidence=1.0,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=cm.ApprovalMetadata(
            "Yeong-hui", FIXED_TIME, "engineering-fixture", "fixture-decision"
        ),
        created_at=FIXED_TIME,
    )
    cm.add_or_merge_memory(characters, character, now=FIXED_TIME)

    contexts = cs.ContextMemoryStore()
    context_evidence = cs.create_context_evidence(
        evidence_type=cs.EvidenceType.SOURCE_OBSERVATION,
        source_case_id="te-v72-stage1251-engineering-fixture",
        source_segment_id="scene-state",
        source_text_hash=_sha("scene-state"),
        excerpt="fixture-scene",
        language="ko",
        observed_at=FIXED_TIME,
    )
    scene = cs.create_scene_memory(
        scene_id="scene-1",
        chapter_id="chapter-1",
        location="estate hall",
        time_state="late evening",
        evidence=context_evidence,
        created_at=FIXED_TIME,
    )
    cs.add_scene(contexts, scene)
    cs.add_scene_participant(
        contexts,
        "scene-1",
        character_id="char-yeonghui",
        participant_status="present",
        presence_confidence=1.0,
        evidence_reference="fixture-scene",
        updated_at=FIXED_TIME,
    )
    speaker = cs.create_context_memory(
        context_type=cs.ContextType.SPEAKER_STATE,
        value="Yeong-hui is the active speaker",
        evidence=context_evidence,
        confidence=1.0,
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=1,
        created_at=FIXED_TIME,
    )
    cs.add_or_merge_context(contexts, speaker, now=FIXED_TIME)
    continuity = cs.create_context_memory(
        context_type=cs.ContextType.SOURCE_CONTEXT_EXCERPT,
        value="The conversation continues after the scene transition",
        evidence=context_evidence,
        confidence=1.0,
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=1,
        created_at=FIXED_TIME,
    )
    cs.add_or_merge_context(contexts, continuity, now=FIXED_TIME)
    return characters, contexts
