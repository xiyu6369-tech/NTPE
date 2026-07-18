from __future__ import annotations

import hashlib
import json
from pathlib import Path

import core.character_memory_v2 as cm
import core.context_scene_memory as cs
from core.translation_quality_integration_v72 import (
    NATURALNESS_POLICY,
    PromptBudget,
    QualityIntegrationFlags,
    QualityIntegrationRequest,
    allocate_prompt_budget,
    integrate_prompt,
)


T0 = "2026-07-19T00:00:00Z"
T1 = "2026-07-19T00:01:00Z"
ROOT = Path(__file__).resolve().parents[2]


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _character_evidence(kind: cm.EvidenceType, segment: str, excerpt: str):
    return cm.create_evidence(
        evidence_type=kind,
        source_case_id="milestone-a",
        source_segment_id=segment,
        source_text_hash=_sha(segment + excerpt),
        excerpt=excerpt,
        language="ko",
        observed_at=T0,
    )


def _character_store() -> cm.MemoryStore:
    store = cm.MemoryStore()
    approved = cm.create_memory(
        character_id="char-yeonghui",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="英熙",
        evidence=_character_evidence(cm.EvidenceType.HUMAN_APPROVED, "name", "영희"),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=cm.ApprovalMetadata("英熙", T0, "reviewer", "decision-name"),
        created_at=T0,
    )
    cm.add_or_merge_memory(store, approved, now=T0)
    style = cm.create_memory(
        character_id="char-yeonghui",
        fact_type=cm.FactType.SPEECH_STYLE,
        value="對長輩使用敬語",
        evidence=_character_evidence(cm.EvidenceType.SOURCE_OBSERVATION, "style", "존댓말"),
        confidence=0.95,
        created_at=T0,
    )
    cm.add_or_merge_memory(store, style, now=T0)
    inferred = cm.create_memory(
        character_id="char-yeonghui",
        fact_type=cm.FactType.PERSONALITY_TRAIT,
        value="可能很生氣",
        evidence=_character_evidence(cm.EvidenceType.AI_INFERENCE, "inference", "추정"),
        confidence=0.99,
        created_at=T0,
    )
    cm.add_or_merge_memory(store, inferred, now=T0)
    irrelevant = cm.create_memory(
        character_id="char-minsu",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="民洙",
        evidence=_character_evidence(cm.EvidenceType.SOURCE_OBSERVATION, "other", "민수"),
        confidence=0.95,
        created_at=T0,
    )
    cm.add_or_merge_memory(store, irrelevant, now=T0)
    return store


def _context_evidence(segment: str, excerpt: str, *, translation: bool = False):
    kind = cs.EvidenceType.TRANSLATION_OBSERVATION if translation else cs.EvidenceType.SOURCE_OBSERVATION
    hashes = {"translation_text_hash": _sha(segment)} if translation else {"source_text_hash": _sha(segment)}
    return cs.create_context_evidence(
        evidence_type=kind,
        source_case_id="milestone-a",
        source_segment_id=segment,
        excerpt=excerpt,
        language="ko",
        observed_at=T0,
        **hashes,
    )


def _context_store() -> cs.ContextMemoryStore:
    store = cs.ContextMemoryStore()
    scene = cs.create_scene_memory(
        scene_id="scene-1",
        chapter_id="chapter-1",
        location="書房",
        time_state="深夜",
        evidence=_context_evidence("scene", "서재"),
        created_at=T0,
    )
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
    cs.add_scene_participant(
        store,
        "scene-1",
        character_id="char-minsu",
        participant_status="present",
        presence_confidence=0.95,
        evidence_reference="exit-evidence",
        updated_at=T1,
    )
    cs.remove_scene_participant(store, "scene-1", character_id="char-minsu", updated_at="2026-07-19T00:02:00Z")
    current = cs.create_context_memory(
        context_type=cs.ContextType.SPEAKER_STATE,
        value="英熙正在說話",
        evidence=_context_evidence("speaker", "영희가 말했다"),
        confidence=0.95,
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=1,
        created_at=T0,
    )
    cs.add_or_merge_context(store, current, now=T0)
    stale = cs.create_context_memory(
        context_type=cs.ContextType.SOURCE_CONTEXT_EXCERPT,
        value="另一場景的內容",
        evidence=_context_evidence("stale", "다른 장면"),
        confidence=0.95,
        chapter_id="chapter-1",
        scene_id="scene-old",
        sequence_index=1,
        created_at=T0,
    )
    cs.add_or_merge_context(store, stale, now=T0)
    return store


def _request(**overrides) -> QualityIntegrationRequest:
    values = dict(
        source_text="영희가 말했다.",
        base_prompt_tokens=500,
        glossary_tokens=20,
        flags=QualityIntegrationFlags(integration=True),
        character_store=_character_store(),
        context_scene_store=_context_store(),
        active_character_ids=("char-yeonghui",),
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=2,
        source_language="ko",
        selection_time="2026-07-19T00:03:00Z",
    )
    values.update(overrides)
    return QualityIntegrationRequest(**values)


def test_character_context_scene_and_naturalness_render_without_internal_evidence() -> None:
    result = integrate_prompt("POLICY\n【韓文】\n영희가 말했다.", _request())
    assert "英熙" in result.section and "對長輩使用敬語" in result.section
    assert "可能很生氣" not in result.section and "民洙" not in result.section
    assert "英熙正在說話" in result.section and "char-minsu" not in result.section
    assert "另一場景的內容" not in result.section
    assert "自然度政策" in result.section
    assert "memory_id" not in result.section and "evidence" not in result.section.lower()


def test_same_input_is_fully_deterministic_across_100_runs() -> None:
    request = _request()
    results = [integrate_prompt("P\n영희가 말했다.", request) for _ in range(100)]
    assert len({item.user_prompt for item in results}) == 1
    assert len({item.metadata.selection_fingerprint for item in results}) == 1


def test_budget_never_truncates_source_and_trims_optional_content() -> None:
    request = _request(budget=PromptBudget(total_prompt_tokens=540, character_tokens=20, context_tokens=20, scene_tokens=20, naturalness_tokens=0))
    result = integrate_prompt("BASE\n영희가 말했다.", request)
    assert result.user_prompt.endswith("영희가 말했다.")
    assert result.metadata.total_added_tokens <= 40
    assert result.metadata.budget_exhausted is True


def test_zero_data_and_disabled_paths_are_clean_noops() -> None:
    prompt = "BASE\n영희가 말했다."
    disabled = integrate_prompt(prompt, _request(flags=QualityIntegrationFlags()))
    empty = integrate_prompt(
        prompt,
        _request(
            flags=QualityIntegrationFlags(character_memory=True, context_scene=True),
            character_store=None,
            context_scene_store=None,
        ),
    )
    assert disabled.user_prompt == prompt and disabled.section == ""
    assert empty.user_prompt == prompt and empty.section == ""


def test_naturalness_policy_obeys_fidelity_and_ambiguity_boundaries() -> None:
    required = ("忠實", "完整", "語意保存", "術語一致", "含混性保存", "不得摘要", "不得自動補全全名", "不得改變否定", "數字或時間")
    assert all(text in NATURALNESS_POLICY for text in required)


def test_budget_allocator_is_deterministic_and_source_reserve_is_untouched() -> None:
    limits = PromptBudget(total_prompt_tokens=800, character_tokens=80, context_tokens=80, scene_tokens=40, naturalness_tokens=80)
    assert allocate_prompt_budget(600, limits, naturalness_text=NATURALNESS_POLICY) == allocate_prompt_budget(600, limits, naturalness_text=NATURALNESS_POLICY)
    assert allocate_prompt_budget(900, limits).available_added == 0


def test_offline_quality_fixture_inventory_covers_all_required_cases() -> None:
    payload = json.loads((ROOT / "tests/fixtures/te_v72_milestone_a/quality_cases.json").read_text(encoding="utf-8"))
    assert payload["provider_execution_required"] is False
    assert len(payload["cases"]) == 16
    assert {row["id"] for row in payload["cases"]} >= {"no-full-name-completion", "negation-preserved", "number-time-preserved", "speaker-continuity"}
