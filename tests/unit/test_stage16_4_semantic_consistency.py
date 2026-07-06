# =====================================================
# NTPE 1.2 Professional - Stage-16.4 Unit Tests
# =====================================================

from core.intelligence import SemanticConsistencyEngine, extract_concepts


def test_extract_concepts_returns_keywords():
    concepts = extract_concepts("鄭泰義 到達 房間 and discovers memory")
    assert "鄭泰義" in concepts


def test_semantic_engine_detects_units_and_metrics():
    engine = SemanticConsistencyEngine()
    result = engine.analyze_texts(["鄭泰義 到達 房間", "鄭泰義 沒有 到達 房間"], source="unit")
    assert result.unit_count == 2
    assert result.metrics["unit_count"] == 2
    assert result.metrics["contradiction_count"] >= 1


def test_semantic_result_is_serializable():
    result = SemanticConsistencyEngine().analyze_text("伊萊 發現 秘密", source="unit")
    data = result.to_dict()
    assert data["units"]
    assert "metrics" in data
