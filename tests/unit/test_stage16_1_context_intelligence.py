# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine Tests
# =====================================================

from core.intelligence import (
    CONTEXT_COMPLETED,
    CONTEXT_COMPRESSED,
    CONTEXT_STARTED,
    ContextEventBus,
    ContextIntelligenceEngine,
    ContextItem,
    ContextRegistry,
    ContextWindow,
)


def test_context_window_selects_by_priority_and_limits():
    window = ContextWindow(max_items=2, max_chars=100)
    window.extend([
        ContextItem(item_id="low", text="低優先", priority=1.0),
        ContextItem(item_id="high", text="高優先", priority=9.0),
        ContextItem(item_id="mid", text="中優先", priority=5.0),
    ])
    assert [item.item_id for item in window.items] == ["high", "mid"]


def test_context_engine_analyze_texts_builds_compressed_context_and_graph():
    engine = ContextIntelligenceEngine(max_items=3, max_chars=500)
    result = engine.analyze_texts(["第一段", "第二段", "第三段"])
    assert result.item_count == 3
    assert "第一段" in result.compressed_context
    assert len(result.edges) == 2
    assert result.metrics["item_count"] == 3


def test_context_event_bus_receives_stage_events():
    bus = ContextEventBus()
    engine = ContextIntelligenceEngine(event_bus=bus)
    engine.analyze_texts(["語境 A", "語境 B"])
    names = [event.name for event in bus.events]
    assert CONTEXT_STARTED in names
    assert CONTEXT_COMPRESSED in names
    assert CONTEXT_COMPLETED in names


def test_context_memory_retains_runtime_items():
    engine = ContextIntelligenceEngine()
    item = engine.build_item("角色先前說過的話", item_id="speaker_1", priority=10, source="character")
    engine.analyze([item])
    assert engine.memory.get("speaker_1") == item


def test_context_registry_lists_bucket_and_all_items():
    registry = ContextRegistry()
    item = ContextItem(item_id="chapter_1", text="章節摘要", priority=4, source="summary")
    registry.register("chapter", item)
    assert registry.list_bucket("chapter") == [item]
    assert registry.list_all() == [item]
