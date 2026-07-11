from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .engine import TranslationDisciplineEngine
from .quality_adapter import UnifiedQualityGateAdapter
from .quality_enforcement import DisciplineQualityEnforcer
from .runtime_orchestrator import orchestrate_runtime_discipline
from .adaptive_retry_policy import build_adaptive_retry_plan
from .audit_trail import build_discipline_audit_trail
from .evidence_retry_integration import integrate_alignment_evidence_for_retry

DISCIPLINE_RUNTIME_INTEGRATION_VERSION = "6.0.0-stage11.3"

QualityRunner = Callable[[str], Mapping[str, Any]]
LegacyQARunner = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
ReportWriter = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class DisciplineRuntimeContext:
    profile: str = "literary"
    qa_attempt: int = 1
    chunk_id: str = ""
    source_text: str = ""
    translated_text: str = ""
    quality_report: Mapping[str, Any] = field(default_factory=dict)
    legacy_qa_report: Mapping[str, Any] = field(default_factory=dict)
    prompt_metadata: Mapping[str, Any] = field(default_factory=dict)
    adaptive_feedback_metadata: Mapping[str, Any] = field(default_factory=dict)
    local_repair_metadata: Mapping[str, Any] = field(default_factory=dict)
    retry_decision_metadata: Mapping[str, Any] = field(default_factory=dict)
    audit_metadata: Mapping[str, Any] = field(default_factory=dict)
    environment_flags: Mapping[str, Any] = field(default_factory=dict)
    runtime_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DisciplineRuntimeResult:
    final_text: str
    initial_quality_report: dict[str, Any]
    final_quality_report: dict[str, Any]
    initial_action: str
    final_action: str
    accepted: bool
    accepted_with_warnings: bool
    provider_retry_required: bool
    rejected: bool
    local_repair_applied: bool
    revalidated: bool
    active_rule_codes: tuple[str, ...]
    matched_issue_codes: tuple[str, ...]
    adaptive_feedback: dict[str, Any]
    audit_report: dict[str, Any]
    metadata: dict[str, Any]
    retry_tier: str = "none"
    adaptive_retry_plan: dict[str, Any] = field(default_factory=dict)
    provider_call_budget: dict[str, int] = field(default_factory=dict)
    targeted_retry_required: bool = False
    full_retry_required: bool = False
    retry_evidence: tuple[dict[str, Any], ...] = ()
    targeted_retry_units: tuple[dict[str, Any], ...] = ()


def _run_quality(
    text: str,
    context: DisciplineRuntimeContext,
    quality_runner: QualityRunner,
    legacy_qa_runner: LegacyQARunner,
) -> dict[str, Any]:
    quality = deepcopy(dict(quality_runner(text) or {}))
    evaluated_text = str(quality.pop("_discipline_final_text", text))
    legacy = deepcopy(dict(legacy_qa_runner(evaluated_text, quality) or {}))
    runtime_qa = legacy or quality
    unified = deepcopy(dict(runtime_qa.get("unified_quality_report") or quality))
    engine = TranslationDisciplineEngine(profile=context.profile)
    enforced = DisciplineQualityEnforcer(UnifiedQualityGateAdapter(engine.feedback)).enforce(unified)
    for issue in enforced.get("merged_issues") or []:
        metadata = issue.get("metadata") or {}
        if (
            str(issue.get("severity") or "").lower() == "critical"
            and not metadata.get("discipline_rule_code")
        ):
            metadata["discipline_route"] = "reject"
            issue["metadata"] = metadata
    runtime_qa["unified_quality_report"] = enforced
    runtime_qa["_discipline_final_text"] = evaluated_text
    return runtime_qa


def integrate_translation_discipline_runtime(
    context: DisciplineRuntimeContext,
    *,
    quality_runner: QualityRunner,
    legacy_qa_runner: LegacyQARunner,
    report_writer: ReportWriter | None = None,
) -> DisciplineRuntimeResult:
    """The sole v6 runtime entrypoint for post-provider discipline handling.

    Callbacks retain ownership of the frozen quality algorithms. This layer only
    coordinates them and never creates a provider client or performs I/O unless
    the caller explicitly supplies a report writer.
    """
    initial_qa = _run_quality(
        context.translated_text, context, quality_runner, legacy_qa_runner
    )
    evaluated_text = str(initial_qa.pop("_discipline_final_text", context.translated_text))

    def revalidate(repaired_text: str) -> Mapping[str, Any]:
        report = _run_quality(repaired_text, context, quality_runner, legacy_qa_runner)
        report.pop("_discipline_final_text", None)
        return report

    outcome = orchestrate_runtime_discipline(
        evaluated_text,
        initial_qa,
        revalidate=revalidate,
    )
    final_qa = outcome.qa_report
    unified = dict(final_qa.get("unified_quality_report") or {})
    evidence_retry = integrate_alignment_evidence_for_retry(
        unified,
        source_text=context.source_text,
        translated_text=outcome.text,
    )
    unified = evidence_retry.report
    final_qa["unified_quality_report"] = unified
    final_qa["evidence_retry_integration"] = evidence_retry.to_metadata()
    plan = build_adaptive_retry_plan(
        unified,
        source_text=context.source_text,
        provider_budget_limit=context.runtime_metadata.get("provider_call_budget_limit"),
        provider_budget_used=int(context.runtime_metadata.get("provider_call_budget_used") or 0),
        post_targeted_retry=bool(context.runtime_metadata.get("post_targeted_retry")),
    )
    plan_metadata = plan.to_metadata()
    # Preserve the frozen Stage 05/09 public action vocabulary. Stage 10
    # exposes the finer route through retry_tier/adaptive_retry_plan.
    final_action = outcome.final_action
    retry = dict(final_qa.get("adaptive_retry_decision") or {})
    audit = dict(final_qa.get("discipline_audit_trail") or {})
    issue_codes = tuple(str(code) for code in retry.get("issue_codes") or ())
    engine = TranslationDisciplineEngine(profile=context.profile)
    adaptive_rules = engine.adaptive_rules(issue_codes)
    adaptive_feedback = {
        **dict(context.adaptive_feedback_metadata),
        "issue_codes": list(issue_codes),
        "discipline_rule_codes": [rule.code for rule in adaptive_rules],
        "discipline_policy_version": engine.metadata()["discipline_policy_version"],
    }
    active_rules = tuple(
        str(code)
        for code in (audit.get("discipline") or {}).get("active_rule_codes") or ()
    )
    integration = {
        "version": DISCIPLINE_RUNTIME_INTEGRATION_VERSION,
        "entrypoint": "core.translation_discipline.runtime_integration",
        "initial_action": outcome.initial_action,
        "final_action": final_action,
        "local_repair_applied": outcome.local_repair_result.changed,
        "revalidated": outcome.revalidated,
        "provider_retry_required": plan.tier in {"targeted_retry", "full_retry"},
        "retry_tier": plan.tier,
        "targeted_retry_required": plan.tier == "targeted_retry",
        "full_retry_required": plan.tier == "full_retry",
        "active_rule_codes": list(active_rules),
        "issue_codes": list(issue_codes),
        "evidence_retry_integration": evidence_retry.to_metadata(),
    }
    final_qa["discipline_runtime_integration"] = integration
    final_qa["adaptive_retry_policy"] = plan_metadata
    final_qa["evidence_retry_integration"] = evidence_retry.to_metadata()
    unified["discipline_runtime_integration"] = integration
    unified["evidence_retry_integration"] = evidence_retry.to_metadata()
    unified["adaptive_retry_policy"] = plan_metadata
    final_qa["unified_quality_report"] = unified
    final_qa["adaptive_feedback"] = adaptive_feedback
    audit = build_discipline_audit_trail(
        final_qa,
        initial_action=outcome.initial_action,
        final_action=final_action,
        revalidated=outcome.revalidated,
        local_repair=outcome.local_repair_result.to_metadata(),
    ).to_metadata()
    final_qa["discipline_audit_trail"] = audit
    final_qa["unified_quality_report"]["discipline_audit_trail"] = audit
    if report_writer is not None:
        report_writer(audit)

    accepted = final_action in {"accept", "accept_with_warnings"}
    return DisciplineRuntimeResult(
        final_text=outcome.text,
        initial_quality_report=initial_qa,
        final_quality_report=final_qa,
        initial_action=outcome.initial_action,
        final_action=final_action,
        accepted=accepted,
        accepted_with_warnings=final_action == "accept_with_warnings",
        provider_retry_required=plan.tier in {"targeted_retry", "full_retry"},
        rejected=final_action == "reject",
        local_repair_applied=outcome.local_repair_result.changed,
        revalidated=outcome.revalidated,
        active_rule_codes=active_rules,
        matched_issue_codes=issue_codes,
        adaptive_feedback=adaptive_feedback,
        audit_report=audit,
        metadata={**dict(context.runtime_metadata), "discipline_runtime_integration": integration, "adaptive_retry_policy": plan_metadata, "evidence_retry_integration": evidence_retry.to_metadata()},
        retry_tier=plan.tier,
        adaptive_retry_plan=plan_metadata,
        provider_call_budget=plan.provider_call_budget.to_metadata(),
        targeted_retry_required=plan.tier == "targeted_retry",
        full_retry_required=plan.tier == "full_retry",
        retry_evidence=tuple(item.to_metadata() for item in plan.retry_evidence),
        targeted_retry_units=tuple(item.to_metadata() for item in plan.targeted_retry_units),
    )
