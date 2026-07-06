from core.intelligence.intelligence_runtime import IntelligenceRuntime
from core.intelligence.intelligence_runtime_context import IntelligenceRuntimeContext
from core.intelligence.intelligence_runtime_events import INTELLIGENCE_RUNTIME_COMPLETED
from core.translation.intelligence_bridge import TranslationIntelligenceBridge


def test_intelligence_runtime_runs_all_default_engines():
    runtime = IntelligenceRuntime()
    result = runtime.analyze(IntelligenceRuntimeContext(source_text="他推開門，回頭看了她一眼。", previous_texts=["夜色很深。"]))
    assert result.metrics["has_context"] is True
    assert result.metrics["has_strategy"] is True
    assert result.selected_strategy


def test_bridge_builds_translation_hints():
    bridge = TranslationIntelligenceBridge()
    result = bridge.prepare("這是一段需要保持語氣的小說對話。", previous_texts=["前一段敘事。"])
    hints = bridge.build_translation_hints(result)
    assert hints["stage"] == "Stage-16.7"
    assert "selected_strategy" in hints


def test_runtime_emits_completion_event():
    runtime = IntelligenceRuntime()
    runtime.analyze("簡短文本。")
    assert runtime.event_bus.events[-1].name == INTELLIGENCE_RUNTIME_COMPLETED
