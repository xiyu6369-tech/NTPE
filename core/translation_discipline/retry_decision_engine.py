from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .local_repair import LocalRepairResult
from .quality_enforcement import discipline_route_codes

RETRY_DECISION_ENGINE_VERSION = "6.0.0-stage05"

ACCEPT = "accept"
ACCEPT_WITH_WARNINGS = "accept_with_warnings"
LOCAL_REPAIR = "local_repair"
PROVIDER_RETRY = "provider_retry"
REJECT = "reject"

_VALID_ACTIONS = frozenset({
    ACCEPT,
    ACCEPT_WITH_WARNINGS,
    LOCAL_REPAIR,
    PROVIDER_RETRY,
    REJECT,
})


def _canonical_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    return code[3:] if code.startswith("V5_") else code


def _issue_codes(report: Mapping[str, Any]) -> set[str]:
    return {
        _canonical_code(issue.get("code") or issue.get("type"))
        for issue in report.get("merged_issues") or []
        if isinstance(issue, Mapping)
    }


def _critical_unrouted_codes(report: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for issue in report.get("merged_issues") or []:
        if not isinstance(issue, Mapping):
            continue
        route = str((issue.get("metadata") or {}).get("discipline_route") or "")
        severity = str(issue.get("severity") or "").strip().lower()
        if severity == "critical" and route not in {"local_repair", "provider_retry"}:
            result.add(_canonical_code(issue.get("code") or issue.get("type")))
    return result


@dataclass(frozen=True)
class RetryDecision:
    action: str
    reason: str
    issue_codes: tuple[str, ...] = ()
    local_repair_codes: tuple[str, ...] = ()
    provider_retry_codes: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    repaired_codes: tuple[str, ...] = ()
    unresolved_local_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.action not in _VALID_ACTIONS:
            raise ValueError(f"invalid retry decision action: {self.action}")

    @property
    def accepted(self) -> bool:
        return self.action in {ACCEPT, ACCEPT_WITH_WARNINGS}

    @property
    def provider_retry_required(self) -> bool:
        return self.action == PROVIDER_RETRY

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": RETRY_DECISION_ENGINE_VERSION,
            "action": self.action,
            "reason": self.reason,
            "accepted": self.accepted,
            "provider_retry_required": self.provider_retry_required,
            "issue_codes": list(self.issue_codes),
            "local_repair_codes": list(self.local_repair_codes),
            "provider_retry_codes": list(self.provider_retry_codes),
            "warning_codes": list(self.warning_codes),
            "repaired_codes": list(self.repaired_codes),
            "unresolved_local_codes": list(self.unresolved_local_codes),
        }


class AdaptiveRetryDecisionEngine:
    """Central decision point for post-quality runtime routing.

    Stage 05 preserves existing score and severity calculation. It only
    centralizes whether the runtime accepts, repairs locally, retries the
    provider, or rejects an unroutable critical result.
    """

    def decide(
        self,
        unified_report: Mapping[str, Any] | None,
        *,
        local_repair_result: LocalRepairResult | None = None,
        post_repair: bool = False,
    ) -> RetryDecision:
        report = dict(unified_report or {})
        codes = _issue_codes(report)
        local_codes = discipline_route_codes(report, "local_repair")
        provider_codes = discipline_route_codes(report, "provider_retry")
        warning_codes = discipline_route_codes(report, "warning")
        repaired_codes = set(local_repair_result.repaired_codes if local_repair_result else ())
        unresolved_codes = set(local_repair_result.unresolved_codes if local_repair_result else ())
        decision = str(report.get("decision") or "").strip().lower()

        critical_unrouted = _critical_unrouted_codes(report)
        if critical_unrouted:
            return RetryDecision(
                action=REJECT,
                reason="Critical quality issues have no safe local or provider-retry route.",
                issue_codes=tuple(sorted(codes)),
                local_repair_codes=tuple(sorted(local_codes)),
                provider_retry_codes=tuple(sorted(provider_codes)),
                warning_codes=tuple(sorted(warning_codes)),
                repaired_codes=tuple(sorted(repaired_codes)),
                unresolved_local_codes=tuple(sorted(unresolved_codes)),
            )

        if provider_codes:
            return RetryDecision(
                action=PROVIDER_RETRY,
                reason="One or more fidelity, completeness, terminology, residue, or repetition issues require provider regeneration.",
                issue_codes=tuple(sorted(codes)),
                local_repair_codes=tuple(sorted(local_codes)),
                provider_retry_codes=tuple(sorted(provider_codes)),
                warning_codes=tuple(sorted(warning_codes)),
                repaired_codes=tuple(sorted(repaired_codes)),
                unresolved_local_codes=tuple(sorted(unresolved_codes)),
            )

        if local_codes and not post_repair and local_repair_result is None:
            return RetryDecision(
                action=LOCAL_REPAIR,
                reason="Only locally routable issues remain; deterministic repair should run before any provider retry.",
                issue_codes=tuple(sorted(codes)),
                local_repair_codes=tuple(sorted(local_codes)),
                warning_codes=tuple(sorted(warning_codes)),
            )

        if decision == "accepted" and not codes:
            action = ACCEPT
            reason = "No quality issues remain."
        elif decision in {"accepted", "accepted_with_warnings"} or codes:
            action = ACCEPT_WITH_WARNINGS if codes else ACCEPT
            reason = (
                "Only non-blocking warnings or locally handled issues remain."
                if codes else "Quality gate accepted the translation."
            )
        elif bool(report.get("retry_required")):
            # Backward-compatible reports may not carry Stage 03 route metadata.
            action = PROVIDER_RETRY
            reason = "Legacy retry-required decision was preserved because no safe local route was available."
        else:
            action = ACCEPT
            reason = "Quality report contains no blocking decision."

        return RetryDecision(
            action=action,
            reason=reason,
            issue_codes=tuple(sorted(codes)),
            local_repair_codes=tuple(sorted(local_codes)),
            provider_retry_codes=tuple(sorted(provider_codes)),
            warning_codes=tuple(sorted(warning_codes)),
            repaired_codes=tuple(sorted(repaired_codes)),
            unresolved_local_codes=tuple(sorted(unresolved_codes)),
        )


def apply_adaptive_retry_decision(
    runtime_qa: Mapping[str, Any],
    *,
    local_repair_result: LocalRepairResult | None = None,
    post_repair: bool = True,
) -> dict[str, Any]:
    """Apply the centralized decision while preserving v5 compatibility fields."""
    result = deepcopy(dict(runtime_qa or {}))
    unified = deepcopy(dict(result.get("unified_quality_report") or {}))
    decision = AdaptiveRetryDecisionEngine().decide(
        unified,
        local_repair_result=local_repair_result,
        post_repair=post_repair,
    )
    metadata = decision.to_metadata()
    unified["adaptive_retry_decision"] = metadata
    result["adaptive_retry_decision"] = metadata

    if decision.action in {ACCEPT, ACCEPT_WITH_WARNINGS}:
        status = "accepted" if decision.action == ACCEPT else "accepted_with_warnings"
        unified.update({
            "decision": status,
            "accepted": True,
            "passed": True,
            "retry_required": False,
            "final_reason": decision.reason,
        })
        result.update({
            "passed": True,
            "status": status,
            "decision": status,
            "retry_required": False,
        })
        if decision.action == ACCEPT_WITH_WARNINGS:
            # Preserve v5 Smart Local Repair consumers and logs.
            compatibility = {
                "stage": "TE-v6.0-stage05",
                "provider_retry_skipped": True,
                "issue_codes": list(decision.issue_codes),
                "local_repairs": [dict(item) for item in (local_repair_result.actions if local_repair_result else ())],
                "decision_engine_version": RETRY_DECISION_ENGINE_VERSION,
            }
            unified["smart_local_repair"] = compatibility
            result["smart_local_repair"] = compatibility
    elif decision.action == PROVIDER_RETRY:
        unified.update({
            "accepted": False,
            "passed": False,
            "retry_required": True,
            "decision": "retry_required",
            "final_reason": decision.reason,
        })
        result.update({
            "passed": False,
            "status": "retry_required",
            "decision": "retry_required",
            "retry_required": True,
        })
    elif decision.action == REJECT:
        unified.update({
            "accepted": False,
            "passed": False,
            "retry_required": False,
            "decision": "rejected",
            "final_reason": decision.reason,
        })
        result.update({
            "passed": False,
            "status": "rejected",
            "decision": "rejected",
            "retry_required": False,
        })

    result["unified_quality_report"] = unified
    return result
