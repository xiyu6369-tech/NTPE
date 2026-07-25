"""Sequential Stage 7.4 orchestration over the existing Stage 7.3 path."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

from core.adaptive_context_authorized_provider_harness import (
    AuthorizedProviderHarnessConfig, AuthorizedSingleInvocationProviderHarness,
)
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_single_real_invocation import (
    FakeSingleInvocationTransport, inspect_translation_output,
)
from core.book_intake import TextCorruptionDetector
from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeDispatchPackage,
    ControlledRuntimeSchedulingDispatchVerificationResult,
)
from core.controlled_translation_runtime_integration.diagnostics import (
    Stage73NvidiaDiagnosticTransport,
)
from core.controlled_translation_runtime_integration.serialization import (
    canonical_json, canonical_sha256,
)
from core.literary import LiteraryPromptBuilder
from core.prompt_contract_verification_canary.candidate_structural_canary import (
    validate_candidate_output,
)
from core.translation_quality_v5 import TranslationQualityBaseline
from core.translation_runtime import format_translation_output
from core.translation_runtime.runtime_output import write_json_output, write_text_output

from .checkpoint import write_checkpoint_atomic
from .errors import (
    ControlledMultiChunkAuthorityError, ControlledMultiChunkOutputError,
    ControlledMultiChunkProviderError, ControlledMultiChunkQualityError,
)
from .models import (
    CheckpointRecord, ChunkCompletionEvidence, ChunkQualityAssessment,
    ChunkQualityVerificationResult, MultiChunkCanaryRequest, MultiChunkResult,
)
from .policy import (
    ATTEMPT_CAP, CHUNK_COUNT, COMBINED_BOUNDARY, CONNECT_TIMEOUT_SECONDS,
    CONTEXT_LIMIT, CREDENTIAL_ENV, FIXED_NAMES, OUTPUT_ROOT, PROFILE, PROVIDER,
    PROVIDER_MODEL, PROVIDER_URL, READ_TIMEOUT_SECONDS, REAL_CANARY_GATE_ENV,
    REQUEST_CAP,
)
from .resolver import resolve_multi_chunk_source
from .verification import (
    verify_chunk_quality_assessment, verify_multi_chunk_result,
)


class ControlledMultiChunkExecutor:
    def __init__(self) -> None:
        self._claimed = False

    def execute(
        self,
        request: MultiChunkCanaryRequest,
        *,
        dispatch_package: ControlledRuntimeDispatchPackage,
        stage72_verification: ControlledRuntimeSchedulingDispatchVerificationResult,
        repository_root: str | Path,
        artifact_root: str | Path,
        execution_mode: str = "fake",
        transport_factory=None,
        environ=None,
    ) -> MultiChunkResult:
        if self._claimed:
            raise ControlledMultiChunkProviderError("executor is single-use")
        if not isinstance(request, MultiChunkCanaryRequest):
            raise TypeError("request must be Stage 7.4 request")
        if (
            not isinstance(
                stage72_verification,
                ControlledRuntimeSchedulingDispatchVerificationResult,
            )
            or not stage72_verification.valid
            or not isinstance(dispatch_package, ControlledRuntimeDispatchPackage)
        ):
            raise ControlledMultiChunkAuthorityError("authentic Stage 7.2 authority required")
        bindings = (
            request.dispatch_package_id == dispatch_package.dispatch_package_id,
            request.dispatch_fingerprint == dispatch_package.dispatch_fingerprint,
            request.schedule_id == dispatch_package.schedule_id,
            request.schedule_fingerprint == dispatch_package.schedule_fingerprint,
            request.queue_record_id == dispatch_package.queue_record_id,
            request.queue_record_fingerprint == dispatch_package.queue_record_fingerprint,
            request.authenticated_lineage == tuple(dispatch_package.canonical_chain),
        )
        if not all(bindings):
            raise ControlledMultiChunkAuthorityError("Stage 7.2 binding mismatch")
        resolved = resolve_multi_chunk_source(dispatch_package, root=repository_root)
        if (
            request.chunk_ids != tuple(plan.chunk_id for plan in resolved.plans)
            or request.chunk_fingerprints
            != tuple(plan.chunk_fingerprint for plan in resolved.plans)
        ):
            raise ControlledMultiChunkAuthorityError("ordered chunk plan mismatch")
        root = Path(artifact_root).resolve()
        repository = Path(repository_root).resolve()
        expected_root = (repository / OUTPUT_ROOT).resolve()
        if root.name.lower() in {"input", "output"}:
            raise ControlledMultiChunkOutputError("formal input/output path forbidden")
        if root != expected_root and execution_mode == "real":
            raise ControlledMultiChunkOutputError("real output root is not isolated Stage 7.4")
        root.mkdir(parents=True, exist_ok=True)
        targets = [
            root / plan.output_artifact_path for plan in resolved.plans
        ] + [
            root / plan.checkpoint_artifact_path for plan in resolved.plans
        ] + [root / "combined.translated.txt", root / "stage74-final-evidence.json"]
        if any(path.exists() for path in targets):
            raise ControlledMultiChunkOutputError("Stage 7.4 target already exists")
        environment = {} if environ is None else environ
        if execution_mode not in {"fake", "real"}:
            raise ValueError("execution_mode must be fake or real")
        if execution_mode == "real" and (
            environment.get(REAL_CANARY_GATE_ENV) != "1"
            or not environment.get(CREDENTIAL_ENV)
            or int(environment.get("NTPE_API_CONNECT_TIMEOUT", "0"))
            != CONNECT_TIMEOUT_SECONDS
            or int(environment.get("NTPE_CURRENT_API_TIMEOUT", "0"))
            != READ_TIMEOUT_SECONDS
        ):
            raise ControlledMultiChunkAuthorityError(
                "real authorization, credential, and 10/180 timeout required"
            )
        self._claimed = True
        completed: list[ChunkCompletionEvidence] = []
        translated_outputs: list[str] = []
        for plan, source_chunk in zip(resolved.plans, resolved.chunks):
            prior_context = (
                translated_outputs[-1][-CONTEXT_LIMIT:] if translated_outputs else ""
            )
            prompt = LiteraryPromptBuilder().build(
                chunk_text=source_chunk,
                locked_dictionary=dict(FIXED_NAMES),
                alias_map={},
                previous_context=prior_context,
                profile=PROFILE,
            )
            payload = {
                "prompt": {
                    "system_prompt": prompt.system_prompt,
                    "user_prompt": prompt.user_prompt,
                },
                "source_fingerprint": plan.chunk_fingerprint,
                "chunk_identity": plan.chunk_id,
            }
            attempt = ProviderAttemptPlan(
                attempt=1,
                model=PROVIDER_MODEL,
                timeout_seconds=READ_TIMEOUT_SECONDS,
                fallback_used=False,
                estimated_input_tokens=max(
                    1, (len(prompt.system_prompt) + len(prompt.user_prompt)) // 3
                ),
                estimated_output_tokens=800,
            )
            transport = (
                transport_factory(plan.index)
                if transport_factory is not None
                else Stage73NvidiaDiagnosticTransport()
                if execution_mode == "real"
                else FakeSingleInvocationTransport()
            )
            if transport.provenance != execution_mode:
                raise ControlledMultiChunkAuthorityError("transport provenance mismatch")
            identity = ProviderRequestIdentity(
                pair_id=f"{request.request_id}-chunk-{plan.index:03d}",
                run_kind="candidate",
                set_name="Stage74_Set",
                chunk_index=1,
                source_hash=plan.chunk_fingerprint,
                chunk_hash=plan.chunk_fingerprint,
                model=PROVIDER_MODEL,
                attempt=1,
                minimum_output_tokens=40,
            )
            harness = AuthorizedSingleInvocationProviderHarness(
                AuthorizedProviderHarnessConfig(
                    boundary_enabled=True,
                    real_provider_enabled=True,
                    authorization_id=request.request_id,
                    execution_mode=execution_mode,
                    provider=PROVIDER,
                    provider_url=PROVIDER_URL,
                    model=PROVIDER_MODEL,
                    session_id=identity.pair_id,
                    single_chunk_only=True,
                    single_controlled_session=True,
                )
            )
            harness_result = harness.run(
                identity=identity,
                payload=payload,
                plans=(attempt,),
                transport=transport,
                environ=environment,
            )
            summary = harness_result.invocation.session.summary
            expected_network = 1 if execution_mode == "real" else 0
            if (
                summary.attempts_executed != 1
                or summary.successful_attempts != 1
                or getattr(transport, "network_requests", 0) != expected_network
            ):
                failure = getattr(transport, "failure", None)
                write_json_output(
                    root / f"chunk-{plan.index:03d}.provider-diagnostic.json",
                    {
                        "schema": "ntpe.controlled_multi_chunk_provider_diagnostic",
                        "version": "1.0",
                        "request_id": request.request_id,
                        "chunk_id": plan.chunk_id,
                        "exception_type": getattr(failure, "exception_type", "RuntimeError"),
                        "cause_type": getattr(failure, "cause_type", ""),
                        "http_status": getattr(failure, "http_status", None),
                        "provider_error_code": getattr(
                            failure, "provider_error_code", ""
                        ),
                        "redacted_message": getattr(
                            failure, "redacted_message", "provider attempt failed"
                        ),
                        "request_count": 1,
                        "attempt_count": 1,
                        "retries": 0,
                        "fallbacks": 0,
                        "no_secret_confirmation": True,
                    },
                )
                raise ControlledMultiChunkProviderError(
                    f"chunk {plan.index} Provider attempt failed"
                )
            raw_output = transport.captured_output
            if not isinstance(raw_output, str):
                raise ControlledMultiChunkProviderError("Provider response was not text")
            translated = format_translation_output(raw_output)
            assessment, metrics = self._quality_assessment(
                source_chunk, translated
            )
            if translated in translated_outputs:
                assessment = replace(
                    assessment,
                    no_duplicate_loop=False,
                    quality_passed=False,
                )
            quality_verification = verify_chunk_quality_assessment(assessment)
            if (
                type(quality_verification) is not ChunkQualityVerificationResult
                or quality_verification.valid is not True
            ):
                reason_codes = (
                    quality_verification.reason_codes
                    if type(quality_verification) is ChunkQualityVerificationResult
                    else ("invalid-quality-verifier-result",)
                )
                write_json_output(
                    root / f"chunk-{plan.index:03d}.quality-diagnostic.json",
                    {
                        "schema": "ntpe.controlled_multi_chunk_quality_diagnostic",
                        "version": "1.0",
                        "request_id": request.request_id,
                        "chunk_id": plan.chunk_id,
                        "assessment": asdict(assessment),
                        "reason_codes": list(reason_codes),
                        "candidate_persisted": False,
                        "no_secret_confirmation": True,
                    },
                )
                raise ControlledMultiChunkQualityError(
                    f"chunk {plan.index} quality gate failed"
                )
            output_path = root / plan.output_artifact_path
            write_text_output(output_path, translated)
            if output_path.read_text(encoding="utf-8") != translated:
                raise ControlledMultiChunkOutputError("chunk output read-back mismatch")
            output_fingerprint = hashlib.sha256(output_path.read_bytes()).hexdigest()
            evidence = ChunkCompletionEvidence(
                request_id=request.request_id,
                request_fingerprint=request.request_fingerprint,
                chunk_id=plan.chunk_id,
                chunk_fingerprint=plan.chunk_fingerprint,
                index=plan.index,
                output_artifact_path=plan.output_artifact_path,
                output_fingerprint=output_fingerprint,
                output_character_count=len(translated),
                context_character_count=len(prior_context),
                context_fingerprint=canonical_sha256(prior_context),
                hangul_character_count=metrics["hangul_character_count"],
                source_echo_detected=metrics["source_echo_detected"],
                duplicate_output_detected=metrics["duplicate_output_detected"],
                corruption_detected=metrics["corruption_detected"],
                traditional_chinese_signal=metrics["traditional_chinese_signal"],
                dialogue_punctuation_passed=metrics["dialogue_punctuation_passed"],
                fixed_names_passed=metrics["fixed_names_passed"],
                quality_passed=True,
            )
            completed.append(evidence)
            translated_outputs.append(translated)
            checkpoint = CheckpointRecord(
                request_id=request.request_id,
                request_fingerprint=request.request_fingerprint,
                source_fixture_id=request.source_fixture_id,
                source_fingerprint=request.source_fingerprint,
                total_planned_chunks=CHUNK_COUNT,
                completed_chunk_count=plan.index,
                completed_chunk_ids=tuple(item.chunk_id for item in completed),
                output_fingerprints=tuple(
                    item.output_fingerprint for item in completed
                ),
                last_completed_chunk_id=plan.chunk_id,
                next_expected_chunk_id=plan.next_chunk_id,
                provider_request_count=plan.index,
                provider_success_count=plan.index,
                translation_execution_count=plan.index,
                artifact_paths=tuple(item.output_artifact_path for item in completed),
            )
            write_checkpoint_atomic(checkpoint, root / plan.checkpoint_artifact_path)
        combined = COMBINED_BOUNDARY.join(translated_outputs)
        combined_path = root / "combined.translated.txt"
        write_text_output(combined_path, combined)
        combined_fingerprint = hashlib.sha256(combined_path.read_bytes()).hexdigest()
        result = MultiChunkResult(
            request_id=request.request_id,
            request_fingerprint=request.request_fingerprint,
            chunk_evidence=tuple(completed),
            combined_output_path=combined_path.name,
            combined_output_fingerprint=combined_fingerprint,
            chunks_planned=3, chunks_started=3, chunks_completed=3,
            provider_requests=3, provider_attempts=3, provider_successes=3,
            translation_executions=3, chunk_outputs_written=3,
            checkpoints_written=3, combined_output_written=1,
        )
        verification = verify_multi_chunk_result(
            request, result, artifact_root=root, raise_on_error=True
        )
        write_json_output(
            root / "stage74-final-evidence.json",
            {
                "schema": "ntpe.controlled_multi_chunk_translation_final_evidence",
                "version": "1.0",
                "request_id": request.request_id,
                "request_fingerprint": request.request_fingerprint,
                "result": asdict(result),
                "result_fingerprint": result.result_fingerprint,
                "verification": asdict(verification),
                "verification_fingerprint": verification.verification_fingerprint,
                "no_secret_confirmation": True,
            },
        )
        return result

    @staticmethod
    def _quality_assessment(source, translated):
        guard = inspect_translation_output(translated, source_length=len(source))
        structural = validate_candidate_output(
            source, translated, success=True, timeout=False
        )
        baseline = TranslationQualityBaseline().evaluate(
            source,
            translated,
            locked_terms=dict(FIXED_NAMES),
            config={
                "max_hangul_residue": 0,
                "max_duplicate_paragraphs": 0,
                "max_duplicate_lines": 1,
            },
        )
        corruption = TextCorruptionDetector().analyze(translated)
        fixed_names = all(
            source_name not in source or target_name in translated
            for source_name, target_name in FIXED_NAMES
        )
        source_echo = bool(
            structural["exact_source_echo"]
            or structural["normalized_source_echo"]
            or structural["partial_source_sequence"]
        )
        duplicate = bool(
            structural["repeated_output_block"]
            or baseline["metrics"]["duplicate_paragraph_count"]
        )
        prohibited_prefix = translated.lstrip().startswith(
            ("譯文：", "翻譯：", "以下是翻譯", "Translation:")
        )
        mandatory = {
            "non_empty": guard.empty_output is False,
            "minimum_output_length_passed": (
                structural["minimum_output_length_passed"] is True
                and guard.suspicious_short_output is False
            ),
            "hangul_residual_passed": (
                structural["hangul_character_count"] == 0
            ),
            "no_source_echo": source_echo is False,
            "no_duplicate_loop": duplicate is False,
            "no_corruption": corruption.status != "blocked",
            "traditional_chinese_signal": (
                structural["traditional_chinese_target_signal"] is True
            ),
            "dialogue_punctuation_passed": (
                baseline["metrics"]["bad_dialogue_quote_count"] == 0
            ),
            "fixed_names_passed": fixed_names is True,
            "no_prohibited_prefix": prohibited_prefix is False,
            "structural_passed": (
                guard.accepted_for_human_review is True
                and structural["candidate_structural_pass"] is True
            ),
            "baseline_passed": baseline["accepted"] is True,
        }
        assessment = ChunkQualityAssessment(
            **mandatory,
            quality_passed=all(value is True for value in mandatory.values()),
        )
        metrics = {
            "hangul_character_count": int(structural["hangul_character_count"]),
            "source_echo_detected": source_echo,
            "duplicate_output_detected": duplicate,
            "corruption_detected": corruption.status == "blocked",
            "traditional_chinese_signal": bool(
                structural["traditional_chinese_target_signal"]
            ),
            "dialogue_punctuation_passed": (
                baseline["metrics"]["bad_dialogue_quote_count"] == 0
            ),
            "fixed_names_passed": fixed_names,
        }
        return assessment, metrics
