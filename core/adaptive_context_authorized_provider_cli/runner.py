from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.adaptive_context_authorized_provider_harness import (
    AuthorizedProviderHarnessResult,
    AuthorizedProviderTransport,
    AuthorizedSingleInvocationProviderHarness,
    FakeAuthorizedProviderTransport,
    write_authorized_harness_report,
)
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity

from .config import CLI_VERSION, AuthorizedProviderCliConfig
from .parser import parse_config
from .report_path import resolve_stage10_report_path


@dataclass(frozen=True)
class AuthorizedProviderCliResult:
    harness_result: AuthorizedProviderHarnessResult
    report_path: str = ""
    network_requests: int = 0
    provider_automatically_executed: bool = False
    comparison_evaluated: bool = False
    readiness_evaluated: bool = False
    content_redacted: bool = True
    version: str = CLI_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_authorized_provider_cli(
    config: AuthorizedProviderCliConfig, *,
    root: str | Path,
    transport: AuthorizedProviderTransport | None = None,
    plans: Sequence[ProviderAttemptPlan] | None = None,
    environ: Mapping[str, str] | None = None,
) -> AuthorizedProviderCliResult:
    blockers = config.validate()
    if blockers:
        raise ValueError(",".join(blockers))
    if transport is None:
        if config.execution_mode == "real":
            raise ValueError("authorized-cli-real-transport-dependency-required")
        transport = FakeAuthorizedProviderTransport()
    if transport.provenance != config.execution_mode:
        raise ValueError("authorized-cli-transport-provenance-mismatch")

    attempt_plans = tuple(plans or (
        ProviderAttemptPlan(1, config.model, 30, False, 100, 80),
    ))
    identity = ProviderRequestIdentity(
        pair_id=config.session_id,
        # Stage 10.2 freezes this legacy label set. It is identity metadata only;
        # this CLI does not create or compare a Baseline artifact.
        run_kind="baseline",
        set_name="Stage10_Authorized_Provider",
        chunk_index=config.chunk_index,
        source_hash=config.source_fingerprint,
        chunk_hash=config.chunk_fingerprint,
        model=config.model,
        attempt=1,
        minimum_output_tokens=10,
    )
    harness_result = AuthorizedSingleInvocationProviderHarness(config.harness_config()).run(
        identity=identity,
        payload={
            "source_fingerprint": config.source_fingerprint,
            "chunk_fingerprint": config.chunk_fingerprint,
            "chunk_index": config.chunk_index,
        },
        plans=attempt_plans,
        transport=transport,
        environ=environ,
    )
    report_path = ""
    if config.report_path:
        target = resolve_stage10_report_path(config.report_path, root=root)
        write_authorized_harness_report(harness_result, target)
        report_path = str(target)
    return AuthorizedProviderCliResult(harness_result=harness_result, report_path=report_path)


def run_from_argv(
    argv: Sequence[str] | None = None, *, root: str | Path,
    transport: AuthorizedProviderTransport | None = None,
    plans: Sequence[ProviderAttemptPlan] | None = None,
    environ: Mapping[str, str] | None = None,
) -> AuthorizedProviderCliResult:
    return run_authorized_provider_cli(
        parse_config(argv), root=root, transport=transport, plans=plans, environ=environ,
    )
