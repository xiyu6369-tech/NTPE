from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from core.adaptive_context_authorized_provider_cli import AuthorizedProviderCliConfig
from core.adaptive_context_authorized_provider_harness import (
    AuthorizedSingleInvocationProviderHarness,
    FakeAuthorizedProviderTransport,
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
    verify_preflight_artifact,
)
from core.literary import LiteraryPromptBuilder
from core.translation_engine.nvidia_client import NvidiaClient
from lts.txt_translation_runtime import split_text

from .config import SingleRealInvocationConfig
from .model import (
    OutputGuardResult,
    SingleRealInvocationArtifact,
    SingleRealInvocationRunResult,
)
from .output_guard import inspect_translation_output
from .report import (
    resolve_invocation_artifact_path,
    resolve_review_path,
    verify_invocation_artifact,
    write_invocation_artifact,
    write_translation_review,
)
from core.production_runtime.manifest import get_te_v7_artifact_path, TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT


class SingleInvocationTransport(Protocol):
    provenance: str
    network_requests: int
    captured_output: object

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> Mapping[str, object]: ...


@dataclass
class FakeSingleInvocationTransport:
    outcomes: tuple[str, ...] = ("success",)
    outputs: tuple[object, ...] = ("這是一段只供 Stage 10.10A 防護驗證使用的虛擬輸出，並不是品質證據。",)
    provenance: str = "fake"
    network_requests: int = 0
    captured_output: object = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        self._transport = FakeAuthorizedProviderTransport(self.outcomes)

    @property
    def calls(self) -> int:
        return self._transport.calls

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> Mapping[str, object]:
        index = self.calls
        outcome = self.outcomes[min(index, len(self.outcomes) - 1)] if self.outcomes else "success"
        if outcome == "exception":
            raise RuntimeError("fake exception content must be redacted")
        result = self._transport.invoke(
            payload, plan, provider_url=provider_url, api_key=api_key,
        )
        if str(result.get("status", "")).lower() in {"success", "accepted"}:
            self.captured_output = self.outputs[min(index, len(self.outputs) - 1)] if self.outputs else ""
        return result


@dataclass
class NvidiaSingleInvocationTransport:
    provenance: str = "real"
    network_requests: int = 0
    captured_output: object = field(default="", init=False, repr=False)

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> Mapping[str, object]:
        prompt = payload.get("prompt", {})
        if not isinstance(prompt, Mapping):
            return {"status": "failed", "error": "provider response format invalid"}
        system_prompt = prompt.get("system_prompt")
        user_prompt = prompt.get("user_prompt")
        if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
            return {"status": "failed", "error": "provider response format invalid"}
        client = NvidiaClient(
            api_key=api_key, api_url=provider_url, timeout=plan.timeout_seconds,
        )
        self.network_requests += 1
        try:
            output = client.chat(
                model=plan.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.12,
                top_p=0.82,
                max_tokens=max(1, plan.estimated_output_tokens),
            )
        except RuntimeError as exc:
            category = str(exc).lower()
            if "timeout" in category:
                raise TimeoutError("provider request timed out") from None
            if "error 503" in category:
                return {"status": "failed", "error": "service unavailable", "http_status": 503}
            if "response format" in category:
                return {"status": "failed", "error": "provider response format invalid"}
            return {"status": "failed", "error": "provider invocation failed"}
        self.captured_output = output
        return {
            "status": "success",
            "provider_model": plan.model,
            "fallback_used": plan.fallback_used,
            "estimated_input_tokens": plan.estimated_input_tokens,
            "estimated_output_tokens": plan.estimated_output_tokens,
            "usage_source": "estimate",
        }


def _blocked(config: SingleRealInvocationConfig, blocker: str) -> SingleRealInvocationRunResult:
    artifact = SingleRealInvocationArtifact(
        stage="TE-v7.0-Stage10.10A",
        status="blocked",
        review_status="not_started",
        chunk_identity="not-executed",
        source_fingerprint="",
        model=config.model,
        attempt_count=0,
        attempts=(),
        total_retry_latency_ms=0.0,
        timeout_detected=False,
        http_503_detected=False,
        fallback_used=False,
        estimated_input_tokens=0,
        estimated_output_tokens=0,
        real_provider_execution=False,
        network_requests=0,
        translation_output_generated=False,
        payload_preserved=False,
        prompt_preserved=False,
        empty_output=True,
        suspicious_short_output=False,
        hangul_residue_signal=False,
        obvious_truncation=False,
        response_format_invalid=False,
        provider_refusal=False,
    )
    return SingleRealInvocationRunResult(artifact=artifact, blockers=(blocker,))


def _load_single_chunk(config: SingleRealInvocationConfig, root: Path) -> str:
    source = Path(config.source_path)
    if not source.is_absolute():
        source = root / source
    expected = (root / "tests/literary/Golden_Set/original_ko.txt").resolve()
    if source.resolve() != expected:
        raise ValueError("single-real-invocation-source-path-not-golden-set")
    chunks = split_text(source.read_text(encoding="utf-8"), config.chunk_size)
    if not chunks or config.chunk_index != 1:
        raise ValueError("single-real-invocation-single-chunk-unavailable")
    return chunks[0]


def _stage109_valid(config: SingleRealInvocationConfig, root: Path) -> bool:
    expected = get_te_v7_artifact_path(root, "te_v7_stage109", TE_V7_STAGE109_REAL_PROVIDER_PREFLIGHT)
    candidate = Path(config.stage109_artifact_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        artifact = verify_preflight_artifact(candidate)
        return candidate.resolve() == expected.resolve() and artifact.eligible and not artifact.provider_executed
    except (OSError, TypeError, ValueError):
        return False


@dataclass
class SingleRealInvocationRunner:
    _claimed: bool = field(default=False, init=False)

    @property
    def claimed(self) -> bool:
        return self._claimed

    def run(
        self, config: SingleRealInvocationConfig, *, root: str | Path,
        environ: Mapping[str, str], transport: SingleInvocationTransport | None = None,
    ) -> SingleRealInvocationRunResult:
        if self._claimed:
            return _blocked(config, "single-real-invocation-session-already-claimed")
        static_blockers = config.validate_static()
        if static_blockers:
            return _blocked(config, static_blockers[0])
        base = Path(root).resolve()
        try:
            artifact_path = resolve_invocation_artifact_path(config.artifact_path, root=base)
            resolve_review_path(config.review_path, root=base)
        except (OSError, ValueError) as exc:
            return _blocked(config, str(exc))
        if not _stage109_valid(config, base):
            return _blocked(config, "single-real-invocation-stage109-integrity-required")
        try:
            source_chunk = _load_single_chunk(config, base)
        except (OSError, UnicodeError, ValueError) as exc:
            return _blocked(config, str(exc))
        source_fingerprint = hashlib.sha256(source_chunk.encode("utf-8")).hexdigest()
        preflight_config = RealProviderPreflightConfig(
            enabled=True,
            boundary_enabled=config.boundary_enabled,
            real_provider_enabled=config.real_provider_enabled,
            authorization_id=config.authorization_id,
            provider=config.provider,
            provider_url=config.provider_url,
            model=config.model,
            fallback_models=tuple(plan.model for plan in config.attempt_plan[1:]),
            attempt_plan=config.attempt_plan,
            max_retries=config.max_retries,
            source_identity=f"{config.session_id}-chunk-001",
            source_fingerprint=source_fingerprint,
            chunk_count=1,
            single_chunk_only=True,
            single_controlled_session=True,
            resumed=False,
        )
        preflight = evaluate_real_provider_preflight(
            preflight_config, root=base, environ=environ,
        )
        if not preflight.artifact.eligible:
            return _blocked(config, f"single-real-invocation-preflight-{preflight.artifact.status}")
        cli_config = AuthorizedProviderCliConfig(
            boundary_enabled=config.boundary_enabled,
            real_provider_enabled=config.real_provider_enabled,
            authorization_id=config.authorization_id,
            execution_mode=config.execution_mode,
            provider=config.provider,
            provider_url=config.provider_url,
            model=config.model,
            session_id=config.session_id,
            source_fingerprint=source_fingerprint,
            chunk_fingerprint=source_fingerprint,
            chunk_index=1,
        )
        cli_blockers = cli_config.validate()
        if cli_blockers:
            return _blocked(config, f"single-real-invocation-stage106-{cli_blockers[0]}")
        if config.execution_mode == "real" and artifact_path.exists():
            try:
                prior = verify_invocation_artifact(artifact_path)
                if prior.real_provider_execution or prior.network_requests > 0:
                    return _blocked(config, "single-real-invocation-already-executed")
            except ValueError:
                return _blocked(config, "single-real-invocation-existing-artifact-integrity-failure")
        active_transport = transport
        if active_transport is None:
            active_transport = (
                NvidiaSingleInvocationTransport()
                if config.execution_mode == "real"
                else FakeSingleInvocationTransport()
            )
        if active_transport.provenance != config.execution_mode:
            return _blocked(config, "single-real-invocation-transport-provenance-mismatch")

        self._claimed = True
        prompt = LiteraryPromptBuilder().build(
            chunk_text=source_chunk,
            locked_dictionary={},
            alias_map={},
            previous_context="",
            profile="literary",
        )
        payload = {
            "prompt": {
                "system_prompt": prompt.system_prompt,
                "user_prompt": prompt.user_prompt,
            },
            "source_fingerprint": source_fingerprint,
            "chunk_identity": "Golden_Set:1",
        }
        plans = tuple(
            ProviderAttemptPlan(
                attempt=plan.attempt,
                model=plan.model,
                timeout_seconds=plan.timeout_seconds,
                fallback_used=plan.fallback_used,
                estimated_input_tokens=max(1, (len(prompt.system_prompt) + len(prompt.user_prompt)) // 3),
                estimated_output_tokens=800,
            )
            for plan in config.attempt_plan
        )
        identity = ProviderRequestIdentity(
            pair_id=config.session_id,
            run_kind="baseline",
            set_name="Golden_Set",
            chunk_index=1,
            source_hash=source_fingerprint,
            chunk_hash=source_fingerprint,
            model=config.model,
            attempt=1,
            minimum_output_tokens=40,
        )
        harness_result = AuthorizedSingleInvocationProviderHarness(
            cli_config.harness_config(),
        ).run(
            identity=identity,
            payload=payload,
            plans=plans,
            transport=active_transport,
            environ=environ,
        )
        evidence = collect_provider_evidence_artifact(
            harness_result,
            ProviderEvidencePipelineConfig(
                enabled=True,
                declared_provenance="real" if config.execution_mode == "real" else "mock",
            ),
        )
        output = active_transport.captured_output
        guard = inspect_translation_output(output, source_length=len(source_chunk))
        real = harness_result.real_provider_execution
        generated = real and isinstance(output, str) and bool(output.strip())
        succeeded = harness_result.invocation.session.summary.successful_attempts > 0
        status = (
            "stage1010a_fake_transport_validated" if not real
            else "single_real_invocation_completed" if succeeded
            else "single_real_invocation_failed"
        )
        artifact = SingleRealInvocationArtifact(
            stage="TE-v7.0-Stage10.10A" if not real else "TE-v7.0-Stage10.10B",
            status=status,
            review_status="awaiting_human_translation_review" if real else "fake_validation_only",
            chunk_identity="Golden_Set:1",
            source_fingerprint=source_fingerprint,
            model=config.model,
            attempt_count=len(evidence.attempts),
            attempts=evidence.attempts,
            total_retry_latency_ms=round(sum(
                row.elapsed_milliseconds or 0.0
                for row in evidence.attempts if row.attempt_number > 1
            ), 3),
            timeout_detected=any(row.timeout for row in evidence.attempts),
            http_503_detected=any(row.http_503 for row in evidence.attempts),
            fallback_used=any(row.fallback_used for row in evidence.attempts),
            estimated_input_tokens=sum(row.estimated_input_tokens for row in evidence.attempts),
            estimated_output_tokens=sum(row.estimated_output_tokens for row in evidence.attempts),
            real_provider_execution=real,
            network_requests=active_transport.network_requests,
            translation_output_generated=generated,
            payload_preserved=harness_result.invocation.session.summary.payload_preserved,
            prompt_preserved=harness_result.invocation.session.summary.prompt_preserved,
            empty_output=guard.empty_output,
            suspicious_short_output=guard.suspicious_short_output,
            hangul_residue_signal=guard.hangul_residue_signal,
            obvious_truncation=guard.obvious_truncation,
            response_format_invalid=guard.response_format_invalid,
            provider_refusal=guard.provider_refusal,
        )
        write_invocation_artifact(artifact, artifact_path, root=base)
        review_text = output if generated and isinstance(output, str) else ""
        if review_text:
            write_translation_review(review_text, config.review_path, root=base)
        return SingleRealInvocationRunResult(
            artifact=artifact, blockers=(), review_text=review_text,
        )
