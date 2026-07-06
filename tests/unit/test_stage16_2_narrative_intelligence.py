# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

import pytest

from core.intelligence import (
    NARRATIVE_ANALYZED,
    NARRATIVE_COMPLETED,
    NARRATIVE_STARTED,
    NarrativeEventBus,
    NarrativeInputError,
    NarrativeIntelligenceEngine,
    NarrativePipeline,
    NarrativeSegment,
    detect_emotional_tone,
    detect_perspective,
    split_segments,
)


def test_narrative_engine_detects_perspective_voice_and_tense():
    engine = NarrativeIntelligenceEngine()
    result = engine.analyze_text("他現在沉默地看著門。\n「你先走。」\n當時他已經下定決心。")
    assert result.perspective == "third_person"
    assert result.voice == "balanced"
    assert result.tense == "past"
    assert result.dialogue_count == 1
    assert result.metrics["segment_count"] == 3


def test_narrative_event_bus_records_stage_events():
    bus = NarrativeEventBus()
    engine = NarrativeIntelligenceEngine(event_bus=bus)
    engine.analyze_text("我現在有些不安。")
    names = [event.name for event in bus.events]
    assert names == [NARRATIVE_STARTED, NARRATIVE_ANALYZED, NARRATIVE_COMPLETED]


def test_narrative_state_tracks_cross_chunk_continuity():
    engine = NarrativeIntelligenceEngine()
    engine.analyze_text("隔天，他已經離開。")
    assert engine.state.last_perspective == "third_person"
    assert engine.state.last_tense == "past"
    assert engine.state.scene_history == ["nar_1"]


def test_narrative_rules_split_dialogue_and_detect_tone():
    segments = split_segments("「別過來。」\n他感到緊張與不安。")
    assert segments[0].kind == "dialogue"
    assert segments[1].kind == "narration"
    assert detect_perspective("我們看著他離開") in {"first_person", "third_person"}
    assert detect_emotional_tone("他緊張得僵住") == "tense"


def test_narrative_pipeline_builds_style_profile_and_findings():
    pipeline = NarrativePipeline()
    result = pipeline.run([
        NarrativeSegment(segment_id="a", text="沒有明確代名詞的描述。", kind="narration"),
        NarrativeSegment(segment_id="b", text="「引號沒有結束", kind="dialogue"),
    ])
    assert result.style_profile["segment_count"] == 2
    assert result.findings
    assert any(finding.category == "dialogue_format" for finding in result.findings)


def test_narrative_engine_rejects_empty_text():
    engine = NarrativeIntelligenceEngine()
    with pytest.raises(NarrativeInputError):
        engine.analyze_text("   ")
