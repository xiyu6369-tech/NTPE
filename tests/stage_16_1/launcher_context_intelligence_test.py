# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine Launcher
# =====================================================

from __future__ import annotations

from core.intelligence import ContextIntelligenceEngine, ContextItem


def run() -> bool:
    engine = ContextIntelligenceEngine(max_items=2, max_chars=200)
    result = engine.analyze([
        ContextItem(item_id="previous", text="鄭泰義先前拒絕了邀請。", priority=5.0, source="previous_chunk"),
        ContextItem(item_id="current", text="下一段接續他的猶豫與對話。", priority=9.0, source="current_chunk"),
        ContextItem(item_id="low", text="較低優先資訊。", priority=1.0, source="metadata"),
    ])
    return (
        result.item_count == 2
        and "current" in result.compressed_context
        and len(result.edges) == 1
        and result.metrics.get("item_count") == 2
    )


if __name__ == "__main__":
    if not run():
        raise SystemExit("Stage-16.1 Launcher FAIL")
    print("Stage-16.1 Launcher PASS")
