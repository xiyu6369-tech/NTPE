from __future__ import annotations

from typing import Any, Mapping

from .models import BaselineShadowComparison


FIELDS = ("prompt_identity", "provider_identity", "language_profile_identity", "context_fingerprint",
          "glossary_fingerprint", "cache_eligibility", "retry_plan", "output_contract",
          "quality_requirement", "planned_request_count")


def compare_baseline_shadow(baseline: Mapping[str, Any], shadow: Mapping[str, Any], *, prompt_budget: int = 768) -> BaselineShadowComparison:
    comparisons = {name: {"baseline": baseline.get(name), "shadow": shadow.get(name),
                          "changed": baseline.get(name) != shadow.get(name)} for name in FIELDS}
    warnings = ()
    blocking = ()
    if int(shadow.get("planned_request_count", 0)) > int(baseline.get("planned_request_count", 0)):
        warnings += ("provider_cost_increase",)
    if int(shadow.get("prompt_additive_tokens", 0)) > prompt_budget:
        blocking += ("prompt_budget_exceeded",)
    if shadow.get("cache_eligibility") and not shadow.get("cache_identity_complete", True):
        blocking += ("cache_identity_incomplete",)
    return BaselineShadowComparison(**comparisons, warnings=warnings, blocking_reasons=blocking)
