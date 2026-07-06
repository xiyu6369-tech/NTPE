# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from core.intelligence import NarrativeEventBus, NarrativeIntelligenceEngine


def run() -> bool:
    bus = NarrativeEventBus()
    engine = NarrativeIntelligenceEngine(event_bus=bus)
    result = engine.analyze_text("""他現在站在門口。
「你真的要走嗎？」
隔天，他已經離開那座城市。""")
    return (
        result.segment_count == 3
        and result.dialogue_count == 1
        and result.perspective == "third_person"
        and result.voice == "balanced"
        and result.metrics.get("scene_transition_count") == 1
        and engine.state.last_perspective == "third_person"
        and len(bus.events) == 3
    )


if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-16.2 Launcher FAIL")
    print("Stage-16.2 Launcher PASS")
