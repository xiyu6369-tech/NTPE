# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from typing import Iterable, List

from .context_graph import ContextGraph
from .context_metrics import build_context_metrics
from .context_result import ContextIntelligenceResult, ContextItem
from .context_window import ContextWindow


class ContextPipeline:
    def __init__(self, *, max_items: int = 8, max_chars: int = 4000) -> None:
        self.max_items = max_items
        self.max_chars = max_chars

    def run(self, items: Iterable[ContextItem]) -> ContextIntelligenceResult:
        window = ContextWindow(max_items=self.max_items, max_chars=self.max_chars)
        window.extend(items)
        selected: List[ContextItem] = list(window.items)
        graph = ContextGraph().build_sequence(selected)
        compressed = window.compress()
        return ContextIntelligenceResult(
            items=selected,
            edges=graph.to_edges(),
            compressed_context=compressed,
            metrics=build_context_metrics(selected, compressed),
        )
