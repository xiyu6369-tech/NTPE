from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from core.adaptive_context_authorized_provider_cli import (
    AuthorizedProviderCliConfig,
    AuthorizedProviderCliResult,
    run_authorized_provider_cli,
)
from core.adaptive_context_authorized_provider_harness import FakeAuthorizedProviderTransport
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence_pipeline import (
    ProviderEvidenceArtifact,
    ProviderEvidencePipelineConfig,
    collect_provider_evidence_artifact,
)

from .contract import FREEZE_VERSION, FakeTransportFreezeContract
from .validator import validate_fake_transport_chain


@dataclass(frozen=True)
class FakeTransportFreezeArtifact:
    status: str
    evidence_status: str
    attempts_recorded: int
    network_requests: int = 0
    real_provider_executed: bool = False
    readiness_evaluated: bool = False
    comparison_executed: bool = False
    content_redacted: bool = True
    payload_preserved: bool = True
    prompt_preserved: bool = True
    stage09_artifacts_unchanged: bool = True
    te_v6_frozen_runtime_unchanged: bool = True
    production_launcher_connected: bool = False
    provider_benchmark_complete: bool = False
    version: str = FREEZE_VERSION


@dataclass(frozen=True)
class FakeTransportFreezeResult:
    cli_result: AuthorizedProviderCliResult
    evidence: ProviderEvidenceArtifact
    artifact: FakeTransportFreezeArtifact


def _snapshot(paths: Sequence[Path]) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in paths:
        if path.is_dir():
            files = sorted(item for item in path.rglob("*") if item.is_file())
        else:
            files = [path] if path.is_file() else []
        for item in files:
            rows[str(item.resolve())] = hashlib.sha256(item.read_bytes()).hexdigest()
    return rows


def run_fake_transport_freeze(
    contract: FakeTransportFreezeContract, *, root: str | Path,
    outcomes: Sequence[str] = ("success",),
    estimated_output_tokens: int = 80,
) -> FakeTransportFreezeResult:
    blockers = contract.validate()
    if blockers:
        raise ValueError(",".join(blockers))
    if not outcomes:
        raise ValueError("provider-execution-freeze-attempt-required")
    base = Path(root).resolve()
    stage09 = base / "artifacts" / "te_v7_stage09"
    te_v6_paths = (
        base / "launcher_translate.py",
        base / "lts" / "txt_translation_runtime.py",
        base / "core" / "translation_runtime" / "runtime_speed_policy.py",
    )
    stage09_before = _snapshot((stage09,))
    te_v6_before = _snapshot(te_v6_paths)
    plans = tuple(
        ProviderAttemptPlan(
            attempt=index,
            model="meta/llama-3.3-70b-instruct",
            timeout_seconds=30 if index == 1 else 60,
            fallback_used=index > 1,
            estimated_input_tokens=100,
            estimated_output_tokens=max(0, int(estimated_output_tokens)),
        )
        for index in range(1, len(outcomes) + 1)
    )
    cli_result = run_authorized_provider_cli(
        AuthorizedProviderCliConfig(
            boundary_enabled=True,
            real_provider_enabled=True,
            authorization_id=contract.authorization_id,
            execution_mode="fake",
            session_id=contract.session_id,
            source_fingerprint=contract.source_fingerprint,
            chunk_fingerprint=contract.chunk_fingerprint,
            chunk_index=1,
        ),
        root=base,
        transport=FakeAuthorizedProviderTransport(tuple(outcomes)),
        plans=plans,
        environ={},
    )
    evidence = collect_provider_evidence_artifact(
        cli_result.harness_result,
        ProviderEvidencePipelineConfig(enabled=True, declared_provenance="mock"),
    )
    chain_blockers = validate_fake_transport_chain(cli_result, evidence)
    stage09_unchanged = stage09_before == _snapshot((stage09,))
    te_v6_unchanged = te_v6_before == _snapshot(te_v6_paths)
    if not stage09_unchanged:
        chain_blockers += ("provider-execution-freeze-stage09-artifact-modified",)
    if not te_v6_unchanged:
        chain_blockers += ("provider-execution-freeze-te-v6-runtime-modified",)
    artifact = FakeTransportFreezeArtifact(
        status="fake_transport_end_to_end_frozen" if not chain_blockers else "freeze_rejected",
        evidence_status=evidence.status,
        attempts_recorded=len(evidence.attempts),
        payload_preserved=evidence.payload_preserved,
        prompt_preserved=evidence.prompt_preserved,
        stage09_artifacts_unchanged=stage09_unchanged,
        te_v6_frozen_runtime_unchanged=te_v6_unchanged,
    )
    if chain_blockers:
        raise ValueError(",".join(chain_blockers))
    return FakeTransportFreezeResult(cli_result=cli_result, evidence=evidence, artifact=artifact)
