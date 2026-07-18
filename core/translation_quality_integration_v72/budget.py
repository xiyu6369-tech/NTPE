from __future__ import annotations

from dataclasses import dataclass

from core.literary.prompt_profiler import estimate_tokens

from .errors import TranslationQualityIntegrationError
from .models import PromptBudget


@dataclass(frozen=True)
class BudgetAllocation:
    character: int
    context: int
    scene: int
    naturalness: int
    available_added: int
    exhausted: bool


def allocate_prompt_budget(base_prompt_tokens: int, limits: PromptBudget, *, naturalness_text: str = "") -> BudgetAllocation:
    values = (limits.total_prompt_tokens, limits.character_tokens, limits.context_tokens, limits.scene_tokens, limits.naturalness_tokens)
    if base_prompt_tokens < 0 or any(isinstance(value, bool) or value < 0 for value in values):
        raise TranslationQualityIntegrationError("prompt budgets must be non-negative integers")
    available = max(0, limits.total_prompt_tokens - base_prompt_tokens)
    remaining = available

    # Naturalness is mandatory policy when requested. Existing source, policy and
    # glossary are already counted in base_prompt_tokens and are never truncated.
    naturalness = min(limits.naturalness_tokens, estimate_tokens(naturalness_text), remaining) if naturalness_text else 0
    remaining -= naturalness
    character = min(limits.character_tokens, remaining)
    remaining -= character
    scene = min(limits.scene_tokens, remaining)
    remaining -= scene
    context = min(limits.context_tokens, remaining)
    requested = (estimate_tokens(naturalness_text) if naturalness_text else 0) + limits.character_tokens + limits.scene_tokens + limits.context_tokens
    return BudgetAllocation(character, context, scene, naturalness, available, available < requested)

