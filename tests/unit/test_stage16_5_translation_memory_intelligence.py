from core.intelligence.translation_memory_engine import TranslationMemoryIntelligenceEngine
from core.intelligence.translation_memory_store import TranslationMemoryStore
from core.intelligence.translation_memory_entry import TranslationMemoryEntry


def test_exact_memory_match():
    engine = TranslationMemoryIntelligenceEngine()
    engine.add_pair("hello world", "哈囉世界")
    result = engine.find_matches("hello world")
    assert result.has_match
    assert result.best_match.match_type == "exact"
    assert result.best_match.score == 1.0


def test_fuzzy_memory_match_with_context():
    engine = TranslationMemoryIntelligenceEngine()
    engine.add_pair("the door opened slowly", "門緩緩地打開了", domain="novel", context_tags=["scene"], character_refs=["A"])
    result = engine.find_matches("the door opened slow", domain="novel", context_tags=["scene"], character_refs=["A"])
    assert result.has_match
    assert result.best_match.score >= 0.72


def test_store_export_import(tmp_path):
    store = TranslationMemoryStore([TranslationMemoryEntry("a", "甲")])
    path = tmp_path / "tm.json"
    store.export_json(path)
    restored = TranslationMemoryStore.import_json(path)
    assert len(restored) == 1
    assert restored.index.exact("a") is not None
