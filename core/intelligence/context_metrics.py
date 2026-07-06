# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

from __future__ import annotations

from typing import Any, Dict, Iterable

from .context_result import ContextItem


def build_context_metrics(items: Iterable[ContextItem], compressed_context: str) -> Dict[str, Any]:
    materialized = list(items)
    return {
        "item_count": len(materialized),
        "total_chars": sum(len(item.text) for item in materialized),
        "compressed_chars": len(compressed_context),
        "sources": sorted({item.source for item in materialized}),
        "max_priority": max((item.priority for item in materialized), default=0.0),
    }
