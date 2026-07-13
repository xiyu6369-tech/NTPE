from __future__ import annotations

from dataclasses import dataclass

from .model import AdaptiveContextResult


@dataclass(frozen=True)
class ContextDiff:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    retained: tuple[str, ...]
    fingerprint_changed: bool


def diff_context(previous: AdaptiveContextResult, current: AdaptiveContextResult) -> ContextDiff:
    before = {row.item_id for row in previous.selected}
    after = {row.item_id for row in current.selected}
    return ContextDiff(tuple(sorted(after - before)), tuple(sorted(before - after)), tuple(sorted(before & after)), previous.fingerprint != current.fingerprint)
