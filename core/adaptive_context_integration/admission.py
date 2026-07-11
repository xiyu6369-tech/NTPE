from __future__ import annotations
from core.adaptive_context import AdaptiveContextResult, ContextItem

def admission_reasons(items: tuple[ContextItem, ...], result: AdaptiveContextResult, baseline_tokens: int) -> tuple[str, ...]:
    reasons: list[str] = []
    selected = {row.item_id for row in result.selected}
    required = {item.item_id for item in items if item.required}
    locked = {item.item_id for item in items if bool(item.metadata.get('locked', False))}
    active_related = {item.item_id for item in items if item.characters}
    if not result.admissible or result.fallback_required:
        reasons.extend(result.fallback_reasons or ('ace-inadmissible',))
    if not required.issubset(selected): reasons.append('required-retention-failed')
    if not locked.issubset(selected): reasons.append('locked-retention-failed')
    if active_related and not (active_related & selected): reasons.append('active-character-retention-failed')
    if items and not result.selected: reasons.append('empty-selection')
    if result.estimated_tokens > result.token_budget: reasons.append('budget-exceeded')
    if result.estimated_tokens >= baseline_tokens: reasons.append('no-token-reduction')
    return tuple(dict.fromkeys(reasons))
