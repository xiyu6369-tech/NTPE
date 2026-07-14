from __future__ import annotations

from collections.abc import Iterable, Mapping

from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_real_provider_boundary import (
    RealProviderBoundaryConfig,
    RealProviderInvocationBoundary,
)

from .config import CREDENTIAL_ENV, AuthorizedProviderHarnessConfig
from .model import AuthorizedProviderHarnessResult
from .transport import AuthorizedProviderTransport


class AuthorizedSingleInvocationProviderHarness:
    def __init__(self, config: AuthorizedProviderHarnessConfig) -> None:
        self.config = config
        self._session_claimed = False

    @property
    def session_claimed(self) -> bool:
        return self._session_claimed

    def run(
        self, *, identity: ProviderRequestIdentity, payload: Mapping[str, object],
        plans: Iterable[ProviderAttemptPlan], transport: AuthorizedProviderTransport,
        environ: Mapping[str, str] | None = None,
    ) -> AuthorizedProviderHarnessResult:
        blockers = list(self.config.validate())
        if self._session_claimed:
            blockers.append("authorized-harness-session-already-claimed")
        if transport.provenance != self.config.execution_mode:
            blockers.append("authorized-harness-transport-provenance-mismatch")
        if identity.chunk_index != 1:
            blockers.append("authorized-harness-single-chunk-identity-required")
        if identity.pair_id != self.config.session_id:
            blockers.append("authorized-harness-session-identity-mismatch")
        if identity.model != self.config.model:
            blockers.append("authorized-harness-model-identity-mismatch")
        if blockers:
            raise ValueError(",".join(blockers))

        plan_rows = tuple(plans)
        if not plan_rows:
            raise ValueError("authorized-harness-attempt-plan-required")

        # Claim before boundary construction so a failed or interrupted call cannot
        # be replayed through the same controlled harness instance.
        self._session_claimed = True
        real = self.config.execution_mode == "real"
        boundary = RealProviderInvocationBoundary(RealProviderBoundaryConfig(
            enabled=True,
            enable_real_provider=real,
            execution_mode=self.config.execution_mode,
            authorization_id=self.config.authorization_id if real else "",
            provider=self.config.provider,
            provider_url=self.config.provider_url,
            model=self.config.model,
            credential_env=CREDENTIAL_ENV,
            pair_id=self.config.session_id,
            run_kind=identity.run_kind,
            single_chunk_only=True,
        ))
        invocation = boundary.run(
            identity=identity,
            payload=payload,
            plans=plan_rows,
            bridge=transport,
            environ=environ,
        )
        return AuthorizedProviderHarnessResult(
            session_id=self.config.session_id,
            execution_provenance=transport.provenance,
            real_provider_execution=invocation.real_provider_execution,
            authorization_confirmed=True,
            boundary_enabled=True,
            real_provider_enabled=True,
            single_chunk_only=True,
            single_controlled_session=True,
            invocation=invocation,
        )
