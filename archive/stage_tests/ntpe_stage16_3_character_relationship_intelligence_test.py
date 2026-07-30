# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence Test
# =====================================================

from core.intelligence import CharacterRelationshipIntelligenceEngine


def main() -> None:
    engine = CharacterRelationshipIntelligenceEngine()
    engine.register_character("鄭泰義", original_name="정태의", aliases=["泰義", "鄭先生"])
    engine.register_character("伊萊", original_name="일라이", aliases=["伊萊・里格勞", "那個男人"])
    engine.add_relationship("鄭泰義", "伊萊", "known")
    result = engine.analyze_texts(["鄭泰義看著伊萊。", "他沒有立刻回答那個男人。"], source="stage16_3")
    assert result.character_count == 2
    assert result.mention_count >= 2
    assert result.metrics["relationship_count"] == 1
    assert "他" in result.pronoun_candidates
    print("Stage-16.3 Launcher PASS")


if __name__ == "__main__":
    main()
