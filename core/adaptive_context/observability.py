from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .model import SelectedContext


def build_context_observability(*, selected: tuple[SelectedContext, ...], omitted_ids: tuple[str, ...], budget: int, admissible: bool = True, fallback_reasons: tuple[str, ...] = ()) -> Mapping[str, object]:
    by_kind: dict[str, int] = {}
    for row in selected:
        by_kind[row.kind] = by_kind.get(row.kind, 0) + 1
    return MappingProxyType({
        "selected_count": len(selected), "omitted_count": len(omitted_ids),
        "selected_ids": tuple(row.item_id for row in selected), "omitted_ids": omitted_ids,
        "selected_by_kind": MappingProxyType(dict(sorted(by_kind.items()))),
        "estimated_tokens": sum(row.estimated_tokens for row in selected), "token_budget": budget,
        "dialogue_preserved": sum(1 for row in selected if row.kind == "dialogue" and row.preserved),
        "narrative_compressed": sum(1 for row in selected if row.kind == "narrative" and row.compressed),
        "raw_context_retained": False,
        "admissible": admissible,
        "fallback_required": not admissible,
        "fallback_reasons": tuple(fallback_reasons),
    })
