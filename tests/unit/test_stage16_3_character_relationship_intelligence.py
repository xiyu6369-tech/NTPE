from core.intelligence import (
    CharacterRelationshipIntelligenceEngine,
    CharacterRegistry,
    build_alias_index,
    detect_alias_conflicts,
    detect_pronouns,
)


def test_character_registry_resolves_aliases():
    registry = CharacterRegistry()
    registry.register("鄭泰義", original_name="정태의", aliases=["泰義"])
    assert registry.resolve("泰義") == "鄭泰義"
    assert registry.resolve("정태의") == "鄭泰義"


def test_character_engine_detects_mentions_and_pronouns():
    engine = CharacterRelationshipIntelligenceEngine()
    engine.register_character("鄭泰義", aliases=["泰義"])
    result = engine.analyze_texts(["泰義回頭。", "他停下腳步。"], source="unit")
    assert result.mention_count == 1
    assert result.pronoun_candidates["他"] == "鄭泰義"


def test_relationship_graph_metrics_are_reported():
    engine = CharacterRelationshipIntelligenceEngine()
    engine.register_character("鄭泰義")
    engine.register_character("伊萊")
    engine.add_relationship("鄭泰義", "伊萊", "known")
    result = engine.analyze_text("鄭泰義和伊萊站在一起。", source="unit")
    assert result.metrics["relationship_count"] == 1
    assert result.character_count == 2


def test_alias_conflict_detection():
    conflicts = detect_alias_conflicts({"A": ["X"], "B": ["X"]})
    assert conflicts == [("X", "A", "B")]
    assert build_alias_index({"A": ["AA"]})["AA"] == "A"


def test_detect_pronouns():
    assert "對方" in detect_pronouns("他看著對方。")
