# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine Launcher
# =====================================================

from core.intelligence import SemanticConsistencyEngine


def main() -> int:
    engine = SemanticConsistencyEngine()
    result = engine.analyze_texts([
        "鄭泰義 到達 房間，並發現伊萊留下的訊息。",
        "鄭泰義 沒有 到達 房間，但仍知道那個訊息。",
    ], source="launcher")
    checks = {
        "Engine Created": engine.name == "Semantic Consistency Engine",
        "Units": result.unit_count == 2,
        "Concept Map": bool(result.concept_map),
        "Metrics": "semantic_consistency_score" in result.metrics,
        "Events": len(engine.event_bus.events) == 3,
    }
    print("NTPE 1.2 Professional - Stage-16.4 Semantic Consistency Engine")
    print("===============================================================")
    for name, ok in checks.items():
        print(f"{name:<24} {'PASS' if ok else 'FAIL'}")
    if not all(checks.values()):
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
