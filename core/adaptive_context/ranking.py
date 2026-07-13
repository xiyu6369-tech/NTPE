from __future__ import annotations

from .model import ContextItem, RankedContext

ACE_KIND_WEIGHTS = {"dialogue": 0.28, "character": 0.24, "glossary": 0.20, "scene": 0.14, "narrative": 0.10, "other": 0.04}


def rank_context(items: list[ContextItem] | tuple[ContextItem, ...], *, active_characters: tuple[str, ...] = ()) -> tuple[RankedContext, ...]:
    active = set(active_characters)
    ranked: list[RankedContext] = []
    for item in items:
        character_match = bool(active.intersection(item.characters))
        score = (
            ACE_KIND_WEIGHTS.get(item.kind, 0.04)
            + 0.25 * _unit(item.relevance)
            + 0.16 * _unit(item.recency)
            + 0.12 * _unit(item.continuity)
            + (0.20 if character_match else 0.0)
            + (1.0 if item.required else 0.0)
        )
        reasons = [item.kind, "required" if item.required else "optional"]
        if character_match:
            reasons.append("active-character")
        ranked.append(RankedContext(item, round(score, 6), tuple(reasons)))
    return tuple(sorted(ranked, key=lambda row: (-row.score, row.item.item_id)))


def _unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
