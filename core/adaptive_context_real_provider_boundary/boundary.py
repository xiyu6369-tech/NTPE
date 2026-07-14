from __future__ import annotations

from collections.abc import Iterable, Mapping
import os

from core.adaptive_context_provider_benchmark_session import (
    ControlledProviderBenchmarkSession, ControlledSessionConfig, ProviderAttemptPlan,
)
from core.adaptive_context_provider_evidence import ProviderRequestIdentity

from .bridge import ProviderInvocationBridge, sanitize_provider_result
from .config import ALLOWED_MODELS, RealProviderBoundaryConfig
from .model import BoundaryInvocationResult


class RealProviderInvocationBoundary:
    def __init__(self, config: RealProviderBoundaryConfig) -> None:
        self.config = config

    def run(
        self, *, identity: ProviderRequestIdentity, payload: Mapping[str, object],
        plans: Iterable[ProviderAttemptPlan], bridge: ProviderInvocationBridge,
        environ: Mapping[str, str] | None = None,
    ) -> BoundaryInvocationResult:
        blockers = list(self.config.validate())
        expected_provenance = self.config.execution_mode
        if bridge.provenance != expected_provenance:
            blockers.append("provider-bridge-provenance-mismatch")
        plan_rows = tuple(plans)
        if any(plan.model not in ALLOWED_MODELS for plan in plan_rows):
            blockers.append("attempt-model-not-allowlisted")
        if identity.model != self.config.model:
            blockers.append("provider-identity-model-mismatch")
        if identity.chunk_index < 1:
            blockers.append("real-provider-boundary-single-chunk-identity-invalid")
        if blockers:
            raise ValueError(",".join(blockers))

        environment = os.environ if environ is None else environ
        api_key = ""
        if self.config.execution_mode == "real":
            api_key = str(environment.get(self.config.credential_env, ""))
            if not api_key:
                raise ValueError("real-provider-environment-credential-required")

        def provider_adapter(provider_payload: dict[str, object], plan: ProviderAttemptPlan) -> dict[str, object]:
            result = bridge.invoke(
                provider_payload, plan, provider_url=self.config.provider_url, api_key=api_key,
            )
            return sanitize_provider_result(result)

        real = self.config.execution_mode == "real"
        session_mode = "mock" if self.config.execution_mode == "fake" else "real"
        session = ControlledProviderBenchmarkSession(ControlledSessionConfig(
            enabled=True, pair_id=self.config.pair_id, run_kind=self.config.run_kind,
            execution_mode=session_mode, real_provider_execution=real,
            single_chunk_only=True,
        )).run(identity=identity, payload=payload, plans=plan_rows, provider=provider_adapter)
        return BoundaryInvocationResult(
            provider=self.config.provider, model=self.config.model,
            execution_provenance=bridge.provenance, real_provider_execution=real,
            authorization_recorded=bool(self.config.authorization_id) if real else False,
            credential_source=self.config.credential_env if real else "not_accessed",
            session=session,
        )
