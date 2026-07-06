# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from typing import Iterable, Sequence

from .context_events import CONTEXT_COMPLETED, CONTEXT_COMPRESSED, CONTEXT_STARTED, ContextEventBus
from .context_memory import ContextMemory
from .context_pipeline import ContextPipeline
from .context_result import ContextIntelligenceResult, ContextItem


class ContextIntelligenceEngine:
    """Public Stage-16.1 facade for deterministic context intelligence."""

    stage = "Stage-16.1"
    name = "Context Intelligence Engine"

    def __init__(self, *, max_items: int = 8, max_chars: int = 4000, event_bus: ContextEventBus | None = None) -> None:
        self.max_items = max_items
        self.max_chars = max_chars
        self.event_bus = event_bus or ContextEventBus()
        self.memory = ContextMemory()

    def build_item(self, text: str, *, item_id: str, priority: float = 1.0, source: str = "runtime", **metadata: object) -> ContextItem:
        return ContextItem(item_id=item_id, text=text, priority=priority, source=source, metadata=dict(metadata))

    def analyze(self, items: Iterable[ContextItem]) -> ContextIntelligenceResult:
        materialized = list(items)
        self.event_bus.emit(CONTEXT_STARTED, item_count=len(materialized), max_items=self.max_items, max_chars=self.max_chars)
        self.memory.remember_many(materialized)
        result = ContextPipeline(max_items=self.max_items, max_chars=self.max_chars).run(materialized)
        self.event_bus.emit(CONTEXT_COMPRESSED, compressed_chars=len(result.compressed_context), selected_items=result.item_count)
        self.event_bus.emit(CONTEXT_COMPLETED, item_count=result.item_count, edge_count=len(result.edges))
        return result

    def analyze_texts(self, texts: Sequence[str], *, source: str = "runtime") -> ContextIntelligenceResult:
        items = [
            ContextItem(item_id=f"ctx_{index + 1}", text=text, priority=float(len(text.strip())), source=source)
            for index, text in enumerate(texts)
            if text and text.strip()
        ]
        return self.analyze(items)
