# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration Launcher
# =====================================================

from core.intelligence.intelligence_runtime import IntelligenceRuntime
from core.intelligence.intelligence_runtime_context import IntelligenceRuntimeContext
from core.translation.intelligence_bridge import TranslationIntelligenceBridge


def main() -> None:
    runtime = IntelligenceRuntime()
    result = runtime.analyze(
        IntelligenceRuntimeContext(
            source_text="鄭泰義看著伊萊，沉默了一會兒才開口。",
            previous_texts=["房間裡很安靜。"],
            terminology={"정태의": "鄭泰義"},
            character_refs=["鄭泰義", "伊萊"],
        )
    )
    assert result.selected_strategy
    assert result.metrics["engine_count"] >= 6
    bridge = TranslationIntelligenceBridge(runtime)
    hints = bridge.build_translation_hints(result)
    assert hints["selected_strategy"] == result.selected_strategy
    print("Stage-16.7 Launcher PASS")


if __name__ == "__main__":
    main()
