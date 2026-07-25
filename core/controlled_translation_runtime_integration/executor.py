"""Stage 7.3 opt-in single-chunk Translation Runtime integration."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from core.adaptive_context_authorized_provider_harness import (
    AuthorizedProviderHarnessConfig, AuthorizedSingleInvocationProviderHarness,
)
from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.adaptive_context_provider_evidence import ProviderRequestIdentity
from core.adaptive_context_single_real_invocation import (
    FakeSingleInvocationTransport, inspect_translation_output,
)
from core.controlled_runtime_scheduling_dispatch import (
    verify_controlled_runtime_scheduling_dispatch,
)
from core.literary import LiteraryPromptBuilder
from core.prompt_contract_verification_canary.candidate_structural_canary import (
    validate_candidate_output,
)
from core.translation_quality_v5 import TranslationQualityBaseline
from core.translation_runtime import format_translation_output
from core.translation_runtime.runtime_output import write_json_output, write_text_output
from core.book_intake import TextCorruptionDetector

from .errors import (
    ControlledTranslationDispatchVerificationError,
    ControlledTranslationOutputError,
    ControlledTranslationProviderConfigurationError,
    ControlledTranslationProviderRequestError,
    ControlledTranslationProviderResponseError,
    ControlledTranslationProviderTimeoutError,
    ControlledTranslationQualityError,
    ControlledTranslationVerificationError,
)
from .diagnostics import (
    Stage73NvidiaDiagnosticTransport, build_provider_diagnostic,
)
from .models import (
    ControlledTranslationExecutionRequest, ControlledTranslationExecutionResult,
    ControlledTranslationOutputEvidence,
)
from .policy import (
    FIXED_NAMES, PROVIDER, PROVIDER_CREDENTIAL_ENV, PROVIDER_MODEL, PROVIDER_URL,
    REAL_CANARY_GATE_ENV,
)
from .resolver import ControlledDispatchWorkPackageResolver
from .verification import verify_controlled_translation_runtime_execution


class ControlledTranslationExecutor:
    def __init__(self, resolver=None):
        self._resolver = resolver or ControlledDispatchWorkPackageResolver()
        self._claimed = False

    def execute(
        self,
        request,
        *,
        dispatch_package,
        schedule,
        stage72_request,
        stage72_result,
        queue_record,
        stage71_request,
        stage71_result,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context,
        repository_root,
        artifact_root,
        execution_mode="fake",
        transport=None,
        environ: Mapping[str, str] | None = None,
        overwrite=False,
    ):
        if not isinstance(request, ControlledTranslationExecutionRequest):
            raise TypeError("request must be Stage 7.3 execution request")
        if self._claimed:
            raise ControlledTranslationProviderRequestError("executor is single-use")
        if type(overwrite) is not bool:
            raise TypeError("overwrite must be bool")
        stage72_verification = verify_controlled_runtime_scheduling_dispatch(
            schedule,
            dispatch_package,
            request=stage72_request,
            result=stage72_result,
            queue_record=queue_record,
            stage71_request=stage71_request,
            stage71_result=stage71_result,
            stage613_claim=stage613_claim,
            stage613_request=stage613_request,
            stage613_result=stage613_result,
            stage613_verification_context=stage613_verification_context,
            persisted_schedule_payload_json=schedule.to_json(),
            persisted_dispatch_payload_json=dispatch_package.to_json(),
            persistence_committed=True,
            schedule_readback_verified=True,
            dispatch_readback_verified=True,
        )
        if type(stage72_verification.valid) is not bool or not stage72_verification.valid:
            raise ControlledTranslationDispatchVerificationError(
                "Stage 7.2 dispatch verification failed"
            )
        self._verify_request_binding(request, dispatch_package)
        work = self._resolver.resolve(dispatch_package, root=repository_root)
        if (
            request.source_fixture_id != work.source_fixture_id
            or request.source_fingerprint != work.source_fingerprint
            or request.work_package_reference_fingerprint
            != work.work_package_reference_fingerprint
            or request.execution_plan_reference_fingerprint
            != work.execution_plan_reference_fingerprint
        ):
            raise ControlledTranslationDispatchVerificationError(
                "resolved work package binding mismatch"
            )
        output_root = Path(artifact_root).resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        output_path = output_root / f"{request.execution_request_id}.translated.txt"
        evidence_path = output_root / f"{request.execution_request_id}.evidence.json"
        if not overwrite and (output_path.exists() or evidence_path.exists()):
            raise ControlledTranslationOutputError("controlled output already exists")
        environment = {} if environ is None else environ
        if execution_mode not in {"fake", "real"}:
            raise ValueError("execution_mode must be fake or real")
        if execution_mode == "real":
            if (
                environment.get(REAL_CANARY_GATE_ENV) != "1"
                or not environment.get(PROVIDER_CREDENTIAL_ENV)
            ):
                raise ControlledTranslationProviderConfigurationError(
                    "real Provider canary is not authorized or configured"
                )
        active_transport = transport
        if active_transport is None:
            active_transport = (
                Stage73NvidiaDiagnosticTransport()
                if execution_mode == "real"
                else FakeSingleInvocationTransport()
            )
        if active_transport.provenance != execution_mode:
            raise ControlledTranslationProviderConfigurationError(
                "Provider transport provenance mismatch"
            )
        prompt = LiteraryPromptBuilder().build(
            chunk_text=work.source_text,
            locked_dictionary=dict(FIXED_NAMES),
            alias_map={},
            previous_context="",
            profile=request.translation_profile,
        )
        payload = {
            "prompt": {
                "system_prompt": prompt.system_prompt,
                "user_prompt": prompt.user_prompt,
            },
            "source_fingerprint": work.source_fingerprint,
            "chunk_identity": request.source_fixture_id,
        }
        plan = ProviderAttemptPlan(
            attempt=1,
            model=PROVIDER_MODEL,
            timeout_seconds=60,
            fallback_used=False,
            estimated_input_tokens=max(
                1, (len(prompt.system_prompt) + len(prompt.user_prompt)) // 3
            ),
            estimated_output_tokens=800,
        )
        identity = ProviderRequestIdentity(
            pair_id=request.execution_request_id,
            run_kind="candidate",
            set_name="Smoke_Set",
            chunk_index=1,
            source_hash=work.source_fingerprint,
            chunk_hash=work.source_fingerprint,
            model=PROVIDER_MODEL,
            attempt=1,
            minimum_output_tokens=40,
        )
        harness = AuthorizedSingleInvocationProviderHarness(
            AuthorizedProviderHarnessConfig(
                boundary_enabled=True,
                real_provider_enabled=True,
                authorization_id=request.execution_request_id,
                execution_mode=execution_mode,
                provider=PROVIDER,
                provider_url=PROVIDER_URL,
                model=PROVIDER_MODEL,
                session_id=request.execution_request_id,
                single_chunk_only=True,
                single_controlled_session=True,
            )
        )
        self._claimed = True
        try:
            harness_result = harness.run(
                identity=identity,
                payload=payload,
                plans=(plan,),
                transport=active_transport,
                environ=environment,
            )
        except TimeoutError as error:
            raise ControlledTranslationProviderTimeoutError(
                "Provider request timed out"
            ) from error
        except (OSError, RuntimeError, ValueError) as error:
            raise ControlledTranslationProviderRequestError(
                "Provider request failed"
            ) from error
        summary = harness_result.invocation.session.summary
        if (
            summary.attempts_executed != 1
            or summary.successful_attempts != 1
            or getattr(active_transport, "network_requests", 0)
            not in ({1} if execution_mode == "real" else {0})
        ):
            if execution_mode == "real" and isinstance(
                active_transport, Stage73NvidiaDiagnosticTransport
            ):
                diagnostic = build_provider_diagnostic(
                    request=request,
                    dispatch_package=dispatch_package,
                    transport=active_transport,
                    provider=PROVIDER,
                    model=PROVIDER_MODEL,
                    provider_url=PROVIDER_URL,
                    authentication_present=bool(
                        environment.get(PROVIDER_CREDENTIAL_ENV)
                    ),
                    max_output_tokens=plan.estimated_output_tokens,
                )
                diagnostic_path = (
                    output_root
                    / f"{request.execution_request_id}.provider-diagnostic.json"
                )
                write_json_output(
                    diagnostic_path, __import__("json").loads(diagnostic.to_json())
                )
                safe_cause = RuntimeError(
                    f"{diagnostic.exception_type}: "
                    f"{diagnostic.redacted_provider_message}"
                )
                raise ControlledTranslationProviderRequestError(
                    "Provider request failed; redacted diagnostic artifact written"
                ) from safe_cause
            raise ControlledTranslationProviderRequestError(
                "one successful Provider attempt was not proven"
            )
        raw_output = active_transport.captured_output
        if not isinstance(raw_output, str):
            raise ControlledTranslationProviderResponseError(
                "Provider response was not text"
            )
        translated = format_translation_output(raw_output)
        guard = inspect_translation_output(
            translated, source_length=work.source_character_count
        )
        structural = validate_candidate_output(
            work.source_text, translated, success=True, timeout=False
        )
        baseline = TranslationQualityBaseline().evaluate(
            work.source_text,
            translated,
            locked_terms=dict(FIXED_NAMES),
            config={
                "max_hangul_residue": 0,
                "max_duplicate_paragraphs": 0,
                "max_duplicate_lines": 1,
            },
        )
        corruption = TextCorruptionDetector().analyze(translated)
        fixed_names_passed = all(
            source not in work.source_text or target in translated
            for source, target in FIXED_NAMES
        )
        quality_passed = all(
            (
                guard.accepted_for_human_review,
                structural["candidate_structural_pass"] is True,
                baseline["accepted"] is True,
                corruption.status != "blocked",
                fixed_names_passed,
            )
        )
        if not quality_passed:
            diagnostic = output_root / f"{request.execution_request_id}.candidate.txt"
            if not diagnostic.exists() or overwrite:
                write_text_output(diagnostic, translated)
            raise ControlledTranslationQualityError("translation quality gate failed")
        try:
            write_text_output(output_path, translated)
        except OSError as error:
            raise ControlledTranslationOutputError("controlled output write failed") from error
        output_fingerprint = hashlib.sha256(output_path.read_bytes()).hexdigest()
        result = ControlledTranslationExecutionResult(
            request=request,
            provider=PROVIDER,
            provider_model=PROVIDER_MODEL,
            output_artifact_path=output_path.name,
            output_artifact_fingerprint=output_fingerprint,
            output_character_count=len(translated),
            quality_passed=True,
            structural_quality_passed=True,
            baseline_quality_passed=True,
            execution_started=True,
            runtime_executor_invoked=True,
            provider_execution_started=True,
            translation_execution_started=True,
            output_written=True,
            runtime_executions_started=1,
            provider_requests=1,
            provider_attempts=1,
            provider_successes=1,
            translation_executions=1,
            controlled_outputs_written=1,
            additional_chunks_started=0,
            retries=0,
            fallbacks=0,
            automatic_rollouts=0,
            formal_output_replacements=0,
            resume_mutations=0,
            cache_mutations=0,
            canonical_chain=tuple(request.upstream_chain)
            + (request.request_fingerprint,),
        )
        metrics = baseline["metrics"]
        evidence = ControlledTranslationOutputEvidence(
            execution_result_id=result.execution_result_id,
            execution_result_fingerprint=result.result_fingerprint,
            execution_request_id=request.execution_request_id,
            execution_request_fingerprint=request.request_fingerprint,
            source_fixture_id=work.source_fixture_id,
            source_fingerprint=work.source_fingerprint,
            source_character_count=work.source_character_count,
            chunk_count=work.chunk_count,
            output_artifact_path=output_path.name,
            output_artifact_fingerprint=output_fingerprint,
            output_character_count=len(translated),
            hangul_character_count=int(structural["hangul_character_count"]),
            hangul_ratio=float(structural["hangul_ratio"]),
            source_echo_detected=bool(
                structural["exact_source_echo"]
                or structural["partial_source_sequence"]
            ),
            duplicate_output_detected=bool(
                structural["repeated_output_block"]
                or metrics["duplicate_paragraph_count"]
            ),
            corruption_detected=corruption.status == "blocked",
            traditional_chinese_signal=bool(
                structural["traditional_chinese_target_signal"]
            ),
            dialogue_punctuation_passed=metrics["bad_dialogue_quote_count"] == 0,
            fixed_names_passed=fixed_names_passed,
            quality_passed=True,
            canonical_chain=tuple(result.canonical_chain),
        )
        try:
            write_json_output(evidence_path, __import__("json").loads(evidence.to_json()))
        except (OSError, ValueError) as error:
            raise ControlledTranslationOutputError("evidence write failed") from error
        verification = verify_controlled_translation_runtime_execution(
            request, result, evidence,
            dispatch_package=dispatch_package,
            artifact_root=output_root,
        )
        if type(verification.valid) is not bool or not verification.valid:
            raise ControlledTranslationVerificationError(
                ",".join(verification.reason_codes)
            )
        return result, evidence

    @staticmethod
    def _verify_request_binding(request, dispatch):
        bindings = {
            "dispatch_package_id": dispatch.dispatch_package_id,
            "dispatch_fingerprint": dispatch.dispatch_fingerprint,
            "schedule_id": dispatch.schedule_id,
            "schedule_fingerprint": dispatch.schedule_fingerprint,
            "scheduling_request_id": dispatch.scheduling_request_id,
            "scheduling_request_fingerprint": dispatch.scheduling_request_fingerprint,
            "queue_record_id": dispatch.queue_record_id,
            "queue_record_fingerprint": dispatch.queue_record_fingerprint,
            "runtime_boundary_id": dispatch.runtime_boundary_id,
            "runtime_boundary_kind": dispatch.runtime_boundary_kind,
            "selected_adapter_index": dispatch.selected_adapter_index,
            "capability_state_fingerprint": dispatch.capability_state_fingerprint,
            "dispatch_key": dispatch.dispatch_key,
            "execution_plan_reference_fingerprint": (
                dispatch.execution_plan_reference_fingerprint
            ),
            "work_package_reference_fingerprint": (
                dispatch.work_package_reference_fingerprint
            ),
        }
        if not all(getattr(request, name) == value for name, value in bindings.items()):
            raise ControlledTranslationDispatchVerificationError(
                "Stage 7.2 dispatch binding mismatch"
            )
        if tuple(request.upstream_chain) != tuple(dispatch.canonical_chain):
            raise ControlledTranslationDispatchVerificationError(
                "Stage 7.2 chain mismatch"
            )
