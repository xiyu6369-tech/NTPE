from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from core.adaptive_context_authorized_provider_harness import (
    AuthorizedProviderHarnessConfig,
    AuthorizedSingleInvocationProviderHarness,
)
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_provider_evidence_pipeline import (
    ProviderEvidencePipelineConfig,
    collect_provider_evidence_artifact,
)
from core.adaptive_context_real_provider_preflight import (
    PreflightAttemptPlan,
    RealProviderPreflightConfig,
    evaluate_real_provider_preflight,
)
from core.adaptive_context_single_real_invocation import (
    FakeSingleInvocationTransport,
    NvidiaSingleInvocationTransport,
    SingleInvocationTransport,
)
from core.literary import LiteraryPromptBuilder
from lts.txt_translation_runtime import split_text

from .config import FROZEN_OUTPUT_TOKEN_BUDGET, ControlledProviderRetryConfig
from .model import ControlledRetryArtifact, ControlledRetryResult
from .report import (
    resolve_controlled_retry_artifact_path,
    resolve_controlled_retry_review_path,
    verify_controlled_retry_artifact,
    write_controlled_retry_artifact,
    write_controlled_retry_review,
)
from .token_evidence import prepared_token_evidence, token_evidence_from_attempt
from .validator import (
    PriorTimeoutEvidence,
    assert_prior_evidence_unchanged,
    validate_prior_timeout_evidence,
)


def _artifact(
    config: ControlledProviderRetryConfig, prior: PriorTimeoutEvidence | None, **changes: object,
) -> ControlledRetryArtifact:
    artifact = prior.artifact if prior is not None else None
    values: dict[str, object] = {
        "stage": "TE-v7.0-Stage10.10.1",
        "status": "blocked",
        "prior_invocation_integrity": prior.file_sha256 if prior else "",
        "prior_invocation_status": artifact.status if artifact else "unavailable",
        "prior_timeout_evidence_valid": prior is not None,
        "prior_timeout_confirmed": bool(artifact and artifact.timeout_detected),
        "prior_network_requests": artifact.network_requests if artifact else 0,
        "invocation_id": config.invocation_id,
        "chunk_identity": "Golden_Set:1",
        "source_fingerprint": artifact.source_fingerprint if artifact else "",
        "model": config.model,
        "timeout_seconds": config.timeout_seconds,
        "attempt_limit": config.attempt_limit,
        "fallback_allowed": config.fallback_allowed,
        "attempt_count": 0,
        "attempts": (),
        "token_evidence": prepared_token_evidence(),
        "timeout_detected": False,
        "http_503_detected": False,
        "real_provider_execution": False,
        "network_requests": 0,
        "retry_executed": False,
        "translation_output_generated": False,
        "payload_preserved": True,
        "prompt_preserved": True,
        "review_status": "not_started",
    }
    values.update(changes)
    return ControlledRetryArtifact(**values)


def _blocked(
    config: ControlledProviderRetryConfig, blocker: str,
    prior: PriorTimeoutEvidence | None = None,
) -> ControlledRetryResult:
    return ControlledRetryResult(_artifact(config, prior), (blocker,))


def _load_chunk(config: ControlledProviderRetryConfig, root: Path) -> str:
    source = Path(config.source_path)
    if not source.is_absolute():
        source = root / source
    expected = (root / "tests/literary/Golden_Set/original_ko.txt").resolve()
    if source.resolve() != expected:
        raise ValueError("controlled-retry-source-path-not-golden-set")
    chunks = split_text(source.read_text(encoding="utf-8"), config.chunk_size)
    if not chunks or config.chunk_index != 1:
        raise ValueError("controlled-retry-golden-chunk-unavailable")
    return chunks[0]


@dataclass
class ControlledProviderRetryRunner:
    _claimed: bool = field(default=False, init=False)

    def _admit(
        self, config: ControlledProviderRetryConfig, *, root: Path,
        environ: Mapping[str, str],
    ) -> tuple[PriorTimeoutEvidence | None, str, str | None]:
        blockers = config.validate_static()
        if blockers:
            return None, "", blockers[0]
        try:
            resolve_controlled_retry_artifact_path(config.artifact_path, root=root)
            resolve_controlled_retry_review_path(config.review_path, root=root)
            prior = validate_prior_timeout_evidence(config, root=root)
            source_chunk = _load_chunk(config, root)
        except (OSError, UnicodeError, ValueError) as exc:
            return None, "", str(exc)
        if not str(environ.get("NVIDIA_API_KEY", "")).strip():
            return prior, source_chunk, "controlled-retry-missing-credential"
        fingerprint = hashlib.sha256(source_chunk.encode("utf-8")).hexdigest()
        if fingerprint != prior.artifact.source_fingerprint:
            return prior, source_chunk, "controlled-retry-source-fingerprint-mismatch"
        preflight = evaluate_real_provider_preflight(
            RealProviderPreflightConfig(
                enabled=True,
                boundary_enabled=True,
                real_provider_enabled=True,
                authorization_id=config.authorization_id,
                provider=config.provider,
                provider_url=config.provider_url,
                model=config.model,
                attempt_plan=(PreflightAttemptPlan(1, config.model, 180, False),),
                max_retries=0,
                source_identity=f"{config.invocation_id}-chunk-001",
                source_fingerprint=fingerprint,
                chunk_count=1,
                single_chunk_only=True,
                single_controlled_session=True,
                resumed=False,
            ),
            root=root,
            environ=environ,
        )
        if not preflight.artifact.eligible:
            return prior, source_chunk, f"controlled-retry-preflight-{preflight.artifact.status}"
        return prior, source_chunk, None

    def prepare(
        self, config: ControlledProviderRetryConfig, *, root: str | Path,
        environ: Mapping[str, str],
    ) -> ControlledRetryResult:
        base = Path(root).resolve()
        prior, _source, blocker = self._admit(config, root=base, environ=environ)
        if blocker:
            return _blocked(config, blocker, prior)
        assert prior is not None
        artifact = _artifact(
            config,
            prior,
            status="controlled_retry_contract_prepared",
            review_status="awaiting_explicit_real_retry_authorization",
        )
        write_controlled_retry_artifact(artifact, config.artifact_path, root=base)
        assert_prior_evidence_unchanged(prior, config, root=base)
        return ControlledRetryResult(artifact)

    def run(
        self, config: ControlledProviderRetryConfig, *, root: str | Path,
        environ: Mapping[str, str], transport: SingleInvocationTransport | None = None,
    ) -> ControlledRetryResult:
        if self._claimed:
            return _blocked(config, "controlled-retry-session-already-claimed")
        base = Path(root).resolve()
        prior, source_chunk, blocker = self._admit(config, root=base, environ=environ)
        if blocker:
            return _blocked(config, blocker, prior)
        assert prior is not None
        artifact_path = resolve_controlled_retry_artifact_path(config.artifact_path, root=base)
        if config.execution_mode == "real" and artifact_path.exists():
            try:
                existing = verify_controlled_retry_artifact(artifact_path)
            except (OSError, TypeError, ValueError):
                return _blocked(config, "controlled-retry-existing-artifact-integrity-failure", prior)
            if existing.real_provider_execution or existing.network_requests:
                return _blocked(config, "controlled-retry-already-executed", prior)
        active_transport = transport
        if active_transport is None:
            active_transport = (
                NvidiaSingleInvocationTransport()
                if config.execution_mode == "real"
                else FakeSingleInvocationTransport()
            )
        if active_transport.provenance != config.execution_mode:
            return _blocked(config, "controlled-retry-transport-provenance-mismatch", prior)

        self._claimed = True
        prompt = LiteraryPromptBuilder().build(
            chunk_text=source_chunk,
            locked_dictionary={},
            alias_map={},
            previous_context="",
            profile="literary",
        )
        fingerprint = hashlib.sha256(source_chunk.encode("utf-8")).hexdigest()
        estimated_input = max(1, (len(prompt.system_prompt) + len(prompt.user_prompt)) // 3)
        payload = {
            "prompt": {
                "system_prompt": prompt.system_prompt,
                "user_prompt": prompt.user_prompt,
            },
            "source_fingerprint": fingerprint,
            "chunk_identity": "Golden_Set:1",
        }
        plan = ProviderAttemptPlan(
            attempt=1,
            model=config.model,
            timeout_seconds=180,
            fallback_used=False,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=FROZEN_OUTPUT_TOKEN_BUDGET,
        )
        identity = ProviderRequestIdentity(
            pair_id=config.invocation_id,
            run_kind="baseline",
            set_name="Golden_Set",
            chunk_index=1,
            source_hash=fingerprint,
            chunk_hash=fingerprint,
            model=config.model,
            attempt=1,
            minimum_output_tokens=40,
        )
        harness = AuthorizedSingleInvocationProviderHarness(
            AuthorizedProviderHarnessConfig(
                boundary_enabled=True,
                real_provider_enabled=True,
                authorization_id=config.authorization_id,
                execution_mode=config.execution_mode,
                provider=config.provider,
                provider_url=config.provider_url,
                model=config.model,
                session_id=config.invocation_id,
            )
        )
        harness_result = harness.run(
            identity=identity,
            payload=payload,
            plans=(plan,),
            transport=active_transport,
            environ=environ,
        )
        evidence = collect_provider_evidence_artifact(
            harness_result,
            ProviderEvidencePipelineConfig(
                enabled=True,
                declared_provenance=("real" if config.execution_mode == "real" else "mock"),
            ),
        )
        raw_attempts = tuple(harness_result.invocation.session.evidence.records)
        first_raw = raw_attempts[0] if raw_attempts else None
        token_evidence = token_evidence_from_attempt(first_raw)
        output = active_transport.captured_output
        real = harness_result.real_provider_execution
        generated = real and isinstance(output, str) and bool(output.strip())
        succeeded = harness_result.invocation.session.summary.successful_attempts > 0
        status = (
            "controlled_retry_contract_prepared"
            if not real
            else "single_controlled_retry_completed"
            if succeeded and generated
            else "single_controlled_retry_failed"
        )
        artifact = _artifact(
            config,
            prior,
            status=status,
            attempt_count=len(evidence.attempts),
            attempts=evidence.attempts,
            token_evidence=token_evidence,
            timeout_detected=any(row.timeout for row in evidence.attempts),
            http_503_detected=any(row.http_503 for row in evidence.attempts),
            real_provider_execution=real,
            network_requests=active_transport.network_requests,
            retry_executed=real,
            translation_output_generated=generated,
            payload_preserved=harness_result.invocation.session.summary.payload_preserved,
            prompt_preserved=harness_result.invocation.session.summary.prompt_preserved,
            review_status=(
                "awaiting_human_translation_review"
                if generated
                else "controlled_retry_not_executed_fake_validation"
                if not real
                else "no_translation_available"
            ),
        )
        assert_prior_evidence_unchanged(prior, config, root=base)
        write_controlled_retry_artifact(artifact, artifact_path, root=base)
        review_text = output if generated and isinstance(output, str) else ""
        if review_text:
            write_controlled_retry_review(review_text, config.review_path, root=base)
        return ControlledRetryResult(artifact, review_text=review_text)
