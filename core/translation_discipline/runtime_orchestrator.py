from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .audit_trail import build_discipline_audit_trail
from .local_repair import LocalRepairResult, apply_adaptive_local_repairs
from .retry_decision_engine import (
    LOCAL_REPAIR,
    AdaptiveRetryDecisionEngine,
    apply_adaptive_retry_decision,
)

RUNTIME_ORCHESTRATOR_VERSION = "6.0.0-stage06"

RevalidateCallback = Callable[[str], Mapping[str, Any]]


@dataclass(frozen=True)
class DisciplineRuntimeOutcome:
    text: str
    qa_report: dict[str, Any]
    local_repair_result: LocalRepairResult
    initial_action: str
    final_action: str
    revalidated: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": RUNTIME_ORCHESTRATOR_VERSION,
            "initial_action": self.initial_action,
            "final_action": self.final_action,
            "revalidated": self.revalidated,
            "local_repair": self.local_repair_result.to_metadata(),
        }


class TranslationDisciplineRuntimeOrchestrator:
    """Single coordination boundary for runtime discipline handling.

    The orchestrator does not define new quality rules. It composes the
    existing Stage 03 quality routes, Stage 04 deterministic local repair and
    Stage 05 centralized retry decision. Runtime-specific quality analysis is
    supplied through a callback so provider, prompt and QA contracts remain
    unchanged.
    """

    def execute(
        self,
        text: str,
        runtime_qa: Mapping[str, Any],
        *,
        revalidate: RevalidateCallback | None = None,
    ) -> DisciplineRuntimeOutcome:
        current_qa = deepcopy(dict(runtime_qa or {}))
        unified = current_qa.get("unified_quality_report") or {}
        initial = AdaptiveRetryDecisionEngine().decide(unified, post_repair=False)

        local_result = LocalRepairResult(text=str(text or ""), changed=False)
        current_text = str(text or "")
        revalidated = False

        if initial.action == LOCAL_REPAIR:
            local_result = apply_adaptive_local_repairs(current_text, unified)
            current_text = local_result.text
            if local_result.changed and revalidate is not None:
                current_qa = deepcopy(dict(revalidate(current_text) or {}))
                revalidated = True

        current_qa = apply_adaptive_retry_decision(
            current_qa,
            local_repair_result=local_result,
            post_repair=True,
        )
        final_action = str((current_qa.get("adaptive_retry_decision") or {}).get("action") or "unknown")

        metadata = {
            "version": RUNTIME_ORCHESTRATOR_VERSION,
            "initial_action": initial.action,
            "final_action": final_action,
            "revalidated": revalidated,
            "local_repair": local_result.to_metadata(),
        }
        current_qa["discipline_runtime_orchestrator"] = metadata
        current_qa.setdefault("unified_quality_report", {})["discipline_runtime_orchestrator"] = metadata
        audit = build_discipline_audit_trail(current_qa, initial_action=initial.action, final_action=final_action, revalidated=revalidated, local_repair=local_result.to_metadata()).to_metadata()
        current_qa["discipline_audit_trail"] = audit
        current_qa.setdefault("unified_quality_report", {})["discipline_audit_trail"] = audit

        return DisciplineRuntimeOutcome(
            text=current_text,
            qa_report=current_qa,
            local_repair_result=local_result,
            initial_action=initial.action,
            final_action=final_action,
            revalidated=revalidated,
        )


def orchestrate_runtime_discipline(
    text: str,
    runtime_qa: Mapping[str, Any],
    *,
    revalidate: RevalidateCallback | None = None,
) -> DisciplineRuntimeOutcome:
    return TranslationDisciplineRuntimeOrchestrator().execute(
        text,
        runtime_qa,
        revalidate=revalidate,
    )
