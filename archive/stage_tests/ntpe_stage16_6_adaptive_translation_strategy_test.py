# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy Launcher
# =====================================================

from core.intelligence.adaptive_strategy_context import AdaptiveStrategyContext
from core.intelligence.adaptive_strategy_engine import AdaptiveTranslationStrategyEngine


def main() -> int:
    engine = AdaptiveTranslationStrategyEngine()
    novel = engine.select_strategy(AdaptiveStrategyContext(source_text="他沉默地看著門外，低聲說：「我知道。」", character_signals={"active": ["鄭泰義"]}))
    tech = engine.select_strategy("API schema config JSON token validation")
    checks = [
        ("Novel Strategy", novel.strategy_name in {"novel_literary", "dialogue_character"}),
        ("Technical Strategy", tech.strategy_name == "technical_precise"),
        ("Confidence", novel.confidence > 0 and tech.confidence > 0),
        ("Explainability", bool(novel.selected.reasons)),
        ("Events", len(engine.event_bus.events) >= 6),
    ]
    print("NTPE Stage-16.6 Adaptive Translation Strategy Test")
    print("====================================================")
    ok = True
    for name, passed in checks:
        print(f"{name:<24} {'PASS' if passed else 'FAIL'}")
        ok = ok and passed
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
