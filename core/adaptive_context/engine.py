from __future__ import annotations

from .budget import calculate_dynamic_budget, estimate_tokens
from .compression import compress_narrative
from .fingerprint import context_fingerprint
from .model import AdaptiveContextResult, ContextItem, SelectedContext
from .observability import build_context_observability
from .preservation import preserve_dialogue
from .ranking import rank_context

ACE_VERSION = "7.0.0-stage01.1"


def build_adaptive_context(items: list[ContextItem] | tuple[ContextItem, ...], *, active_characters: tuple[str, ...] = (), model_context_limit: int = 8192, fixed_prompt_tokens: int = 0, source_tokens: int = 0, reserved_output_tokens: int = 1024, requested_context_tokens: int | None = None) -> AdaptiveContextResult:
    item_rows = tuple(items)
    ids = [item.item_id for item in item_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("context item_id values must be unique")
    budget = calculate_dynamic_budget(model_context_limit=model_context_limit, fixed_prompt_tokens=fixed_prompt_tokens, source_tokens=source_tokens, reserved_output_tokens=reserved_output_tokens, requested_context_tokens=requested_context_tokens)
    selected: list[SelectedContext] = []
    omitted: list[str] = []
    remaining = budget.available_tokens
    for ranked in rank_context(item_rows, active_characters=active_characters):
        item = ranked.item
        original_tokens = estimate_tokens(item.content)
        if item.required and original_tokens > remaining:
            reason = f"required-context-overflow:{item.item_id}"
            omitted_ids = tuple(sorted(ids))
            observation = build_context_observability(selected=(), omitted_ids=omitted_ids, budget=budget.available_tokens, admissible=False, fallback_reasons=(reason,))
            return AdaptiveContextResult(ACE_VERSION, (), omitted_ids, budget.available_tokens, 0, context_fingerprint(()), observation, False, True, (reason,))
        content = item.content
        compressed = False
        preserved = item.kind == "dialogue"
        if original_tokens > remaining:
            if item.kind == "dialogue":
                content = preserve_dialogue(item.content, remaining)
            elif item.kind == "narrative":
                content = compress_narrative(item.content, remaining)
                compressed = content != " ".join(item.content.split())
            else:
                content = ""
        used = estimate_tokens(content)
        if not content or used > remaining:
            omitted.append(item.item_id)
            continue
        selected.append(SelectedContext(item.item_id, item.kind, content, used, ranked.score, preserved, compressed))
        remaining -= used
    rows = tuple(selected)
    omitted_ids = tuple(sorted(omitted))
    observation = build_context_observability(selected=rows, omitted_ids=omitted_ids, budget=budget.available_tokens)
    return AdaptiveContextResult(ACE_VERSION, rows, omitted_ids, budget.available_tokens, sum(row.estimated_tokens for row in rows), context_fingerprint(rows), observation, True, False, ())
