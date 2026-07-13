from __future__ import annotations

from typing import Iterable, Mapping

from core.adaptive_context_provider_evidence import (
    ProviderEvidenceCollector, ProviderEvidenceConfig, ProviderRequestIdentity,
)

from .attempt_runner import run_caller_owned_attempts
from .config import ControlledSessionConfig
from .model import ProviderAttemptPlan, SessionSummary
from .provider_bridge import ProviderCallable
from .result import ControlledSessionResult


class ControlledProviderBenchmarkSession:
    def __init__(self, config: ControlledSessionConfig) -> None:
        self.config = config

    def run(
        self, *, identity: ProviderRequestIdentity, payload: Mapping[str, object],
        plans: Iterable[ProviderAttemptPlan], provider: ProviderCallable,
    ) -> ControlledSessionResult:
        blockers = self.config.validate()
        if blockers:
            raise ValueError(",".join(blockers))
        if identity.pair_id != self.config.pair_id or identity.run_kind != self.config.run_kind:
            raise ValueError("controlled-session-identity-contract-mismatch")
        plan_rows = tuple(plans)
        if not plan_rows:
            raise ValueError("controlled-session-attempt-plan-required")
        if tuple(plan.attempt for plan in plan_rows) != tuple(range(1, len(plan_rows) + 1)):
            raise ValueError("controlled-session-attempt-plan-order-invalid")
        collector = ProviderEvidenceCollector(ProviderEvidenceConfig(
            enabled=True, pair_id=self.config.pair_id, run_kind=self.config.run_kind,
            real_provider_execution=self.config.real_provider_execution,
        ))
        executed, payload_ok, prompt_ok = run_caller_owned_attempts(
            collector=collector, identity=identity, payload=payload, plans=plan_rows, provider=provider,
        )
        evidence = collector.bundle()
        records = evidence.records
        success = sum(row.status in {"success", "accepted"} for row in records)
        timeout = sum(row.error_category == "timeout" for row in records)
        http_503 = sum(row.http_status == 503 for row in records)
        failed = len(records) - success
        if identity.resumed:
            state = "excluded"
        elif success:
            state = "completed"
        elif records and all(row.external_provider_condition for row in records):
            state = "provider_limited"
        else:
            state = "failed"
        summary = SessionSummary(
            pair_id=self.config.pair_id, run_kind=self.config.run_kind, state=state,
            attempts_planned=len(plan_rows), attempts_executed=executed,
            successful_attempts=success, failed_attempts=failed, timeout_attempts=timeout,
            http_503_attempts=http_503, total_latency_ms=collector.total_latency_ms(),
            payload_preserved=payload_ok, prompt_preserved=prompt_ok,
        )
        result_blockers: list[str] = []
        if not payload_ok: result_blockers.append("provider-bridge-payload-mutated")
        if not prompt_ok: result_blockers.append("provider-bridge-prompt-mutated")
        return ControlledSessionResult(
            summary=summary, evidence=evidence, blockers=tuple(result_blockers),
            limitations=("session-does-not-evaluate-stage10-readiness",),
        )
