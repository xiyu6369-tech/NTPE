from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Mapping

from .retry_evidence import RetryEvidence, canonical_issue_code, collect_retry_evidence
from .targeted_retry_plan import TargetedRetryUnit, build_targeted_retry_units

ADAPTIVE_RETRY_POLICY_VERSION = "6.0.0-stage10"

NONE = "none"
TARGETED_RETRY = "targeted_retry"
FULL_RETRY = "full_retry"

LOCAL_REPAIR_CODES = frozenset({"SIMPLIFIED_CHINESE", "DIALOGUE_QUOTE_FORMAT", "FORMATTING"})
WARNING_ONLY_CODES = frozenset({"NATURALNESS_GUARD", "PARAGRAPH_STRUCTURE_MERGED"})
TARGETABLE_CODES = frozenset({
    "PARAGRAPH_OMISSION_SUSPECTED", "SENTENCE_OMISSION_SUSPECTED",
    "SEMANTIC_DUPLICATE_PARAGRAPH", "DUPLICATE_PARAGRAPH",
    "LOCKED_TERM_MISSING", "HANGUL_RESIDUE",
})
FULL_RETRY_CODES = frozenset({
    "EMPTY_OUTPUT", "TOO_SHORT", "HALLUCINATION", "ADDED_DETAIL",
    "GLOBAL_SEMANTIC_DRIFT", "GLOBAL_ORDER_DISRUPTION", "QUALITY_LOCK_VIOLATION",
    "MULTI_PARAGRAPH_HALLUCINATION", "WIDESPREAD_TERMINOLOGY_FAILURE",
})


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class ProviderCallBudget:
    limit: int = 2
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def can_spend(self, count: int = 1) -> bool:
        return count >= 0 and count <= self.remaining

    def spend(self, count: int = 1) -> "ProviderCallBudget":
        if not self.can_spend(count):
            raise ValueError("chunk provider recovery budget exceeded")
        return ProviderCallBudget(self.limit, self.used + count)

    def to_metadata(self) -> dict[str, int]:
        return {"limit": self.limit, "used": self.used, "remaining": self.remaining}


@dataclass(frozen=True)
class AdaptiveRetryPlan:
    version: str = ADAPTIVE_RETRY_POLICY_VERSION
    tier: str = NONE
    action: str = NONE
    issue_codes: tuple[str, ...] = ()
    local_repair_codes: tuple[str, ...] = ()
    targeted_retry_units: tuple[TargetedRetryUnit, ...] = ()
    full_retry_codes: tuple[str, ...] = ()
    provider_call_budget: ProviderCallBudget = field(default_factory=ProviderCallBudget)
    fallback_action: str = FULL_RETRY
    reason: str = ""
    retry_evidence: tuple[RetryEvidence, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "tier": self.tier,
            "action": self.action,
            "issue_codes": list(self.issue_codes),
            "local_repair_codes": list(self.local_repair_codes),
            "targeted_retry_units": [unit.to_metadata() for unit in self.targeted_retry_units],
            "full_retry_codes": list(self.full_retry_codes),
            "provider_call_budget": self.provider_call_budget.to_metadata(),
            "fallback_action": self.fallback_action,
            "reason": self.reason,
            "retry_evidence": [item.to_metadata() for item in self.retry_evidence],
            "metadata": dict(self.metadata),
        }


class AdaptiveRetryPolicy:
    def plan(
        self,
        unified_report: Mapping[str, Any] | None,
        *,
        source_text: str = "",
        provider_budget_limit: int | None = None,
        provider_budget_used: int = 0,
        post_targeted_retry: bool = False,
    ) -> AdaptiveRetryPlan:
        report = dict(unified_report or {})
        issues = [item for item in report.get("merged_issues") or () if isinstance(item, Mapping)]
        codes = tuple(sorted({canonical_issue_code(item.get("code") or item.get("type")) for item in issues}))
        budget = ProviderCallBudget(
            limit=provider_budget_limit if provider_budget_limit is not None else _env_int("NTPE_CHUNK_PROVIDER_BUDGET", 2, 0, 20),
            used=max(0, int(provider_budget_used)),
        )
        critical_unknown = tuple(sorted({
            canonical_issue_code(item.get("code") or item.get("type")) for item in issues
            if str(item.get("severity") or "").lower() == "critical"
            and canonical_issue_code(item.get("code") or item.get("type")) not in LOCAL_REPAIR_CODES | WARNING_ONLY_CODES | TARGETABLE_CODES | FULL_RETRY_CODES
        }))
        if critical_unknown:
            return AdaptiveRetryPlan(tier="reject", action="reject", issue_codes=codes, provider_call_budget=budget, reason="Unknown critical issue has no safe recovery policy.")
        blocking = [item for item in issues if bool(item.get("retry_required") or item.get("retry_worthy")) or str(item.get("severity") or "").lower() in {"critical", "high"}]
        blocking_codes = {canonical_issue_code(item.get("code") or item.get("type")) for item in blocking}
        if not issues:
            return AdaptiveRetryPlan(issue_codes=codes, provider_call_budget=budget, reason="No quality issues remain.")
        if not blocking_codes:
            local = tuple(sorted(set(codes) & LOCAL_REPAIR_CODES))
            tier = "local_repair" if local else NONE
            return AdaptiveRetryPlan(tier=tier, action=tier, issue_codes=codes, local_repair_codes=local, provider_call_budget=budget, reason="Only deterministic local repair or warning-only issues remain.")
        local = tuple(sorted(blocking_codes & LOCAL_REPAIR_CODES))
        full = tuple(sorted(blocking_codes & FULL_RETRY_CODES))
        if full or post_targeted_retry:
            return AdaptiveRetryPlan(tier=FULL_RETRY, action=FULL_RETRY, issue_codes=codes, local_repair_codes=local, full_retry_codes=full or tuple(sorted(blocking_codes)), provider_call_budget=budget, fallback_action="reject" if not budget.remaining else FULL_RETRY, reason="A blocking issue cannot be safely resolved by targeted recovery.")
        evidence = collect_retry_evidence(report, source_text)
        targeted_codes = blocking_codes & TARGETABLE_CODES
        targeted_evidence = tuple(item for item in evidence if item.issue_code in targeted_codes)
        units = build_targeted_retry_units(
            source_text, targeted_evidence,
            max_units=min(budget.remaining, _env_int("NTPE_TARGETED_RETRY_MAX_UNITS", 2, 0, 20)),
            attempts_per_unit=_env_int("NTPE_TARGETED_RETRY_ATTEMPTS", 1, 1, 3),
        )
        reliable_codes = {code for unit in units for code in unit.reason_codes}
        if targeted_codes and reliable_codes == targeted_codes and units and budget.remaining:
            return AdaptiveRetryPlan(tier=TARGETED_RETRY, action=TARGETED_RETRY, issue_codes=codes, local_repair_codes=local, targeted_retry_units=units, provider_call_budget=budget, fallback_action=FULL_RETRY, reason="Reliable issue evidence identifies bounded source ranges.", retry_evidence=targeted_evidence)
        unresolved = tuple(sorted(blocking_codes - set(local)))
        return AdaptiveRetryPlan(tier=FULL_RETRY, action=FULL_RETRY, issue_codes=codes, local_repair_codes=local, full_retry_codes=unresolved, provider_call_budget=budget, fallback_action="reject" if not budget.remaining else FULL_RETRY, reason="Blocking issues lack reliable bounded evidence for targeted recovery.", retry_evidence=targeted_evidence)


def build_adaptive_retry_plan(unified_report: Mapping[str, Any] | None, **kwargs: Any) -> AdaptiveRetryPlan:
    return AdaptiveRetryPolicy().plan(unified_report, **kwargs)
