from __future__ import annotations

from collections.abc import Iterable

from .config import IMPLEMENTATION_STATUS, PROMPT_SECTIONS, RISK_LEVELS
from .model import PromptImprovementPlan


def validate_plans(plans: Iterable[PromptImprovementPlan]) -> tuple[PromptImprovementPlan, ...]:
    rows = tuple(plans)
    ids = [row.plan_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate prompt improvement plan id")
    for row in rows:
        if row.target_prompt_section not in PROMPT_SECTIONS:
            raise ValueError("unsupported prompt section")
        if row.risk_level not in RISK_LEVELS:
            raise ValueError("unsupported plan risk")
        if not row.requires_human_approval or row.implementation_status != IMPLEMENTATION_STATUS:
            raise ValueError("prompt plan may not be approved or applied automatically")
        if not row.related_defect_ids:
            raise ValueError("prompt plan requires defect evidence")
    return rows
