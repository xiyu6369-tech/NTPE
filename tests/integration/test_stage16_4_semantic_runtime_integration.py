# =====================================================
# NTPE 1.2 Professional - Stage-16.4 Integration Tests
# =====================================================

from core.intelligence import (
    CharacterRelationshipIntelligenceEngine,
    ContextIntelligenceEngine,
    NarrativeIntelligenceEngine,
    SemanticConsistencyEngine,
)


def test_semantic_layer_coexists_with_stage16_engines():
    context = ContextIntelligenceEngine()
    narrative = NarrativeIntelligenceEngine()
    character = CharacterRelationshipIntelligenceEngine()
    semantic = SemanticConsistencyEngine()
    character.register_character("鄭泰義", aliases=["伊萊"])

    text = "鄭泰義 到達 房間。他發現伊萊留下的訊息。"
    assert context.analyze_texts([text]).item_count == 1
    assert narrative.analyze_text(text).segment_count >= 1
    assert character.analyze_text(text).mention_count >= 1
    assert semantic.analyze_text(text).unit_count == 1


def test_semantic_events_are_emitted():
    engine = SemanticConsistencyEngine()
    engine.analyze_texts(["凱爾 離開 房間", "凱爾 回來 房間"], source="integration")
    assert [event.name for event in engine.event_bus.events] == [
        "SemanticStarted",
        "SemanticAnalyzed",
        "SemanticCompleted",
    ]
