"""Official Stage 7.3 output and governance verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import ControlledTranslationVerificationError
from .models import (
    ControlledTranslationExecutionRequest, ControlledTranslationExecutionResult,
    ControlledTranslationOutputEvidence, ControlledTranslationVerificationResult,
    _id,
)
from .policy import (
    EVIDENCE_SCHEMA_NAME, EVIDENCE_SCHEMA_VERSION, REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION, RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION,
)
from .serialization import canonical_sha256, values


def verify_controlled_translation_runtime_execution(
    request,
    result,
    evidence,
    *,
    dispatch_package,
    artifact_root,
    raise_on_error=False,
):
    if not isinstance(request, ControlledTranslationExecutionRequest):
        raise TypeError("request must be Stage 7.3 request")
    if not isinstance(result, ControlledTranslationExecutionResult):
        raise TypeError("result must be Stage 7.3 result")
    if not isinstance(evidence, ControlledTranslationOutputEvidence):
        raise TypeError("evidence must be Stage 7.3 evidence")
    schema_ok = (
        (request.schema_name, request.schema_version)
        == (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION)
        and (result.schema_name, result.schema_version)
        == (RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION)
        and (evidence.schema_name, evidence.schema_version)
        == (EVIDENCE_SCHEMA_NAME, EVIDENCE_SCHEMA_VERSION)
    )
    request_id = _id(
        "stage73-execution-request",
        values(request, exclude=("execution_request_id", "request_fingerprint")),
    )
    request_fp = canonical_sha256(values(request, exclude=("request_fingerprint",)))
    pre_result = tuple(result.canonical_chain[:39])
    result_id = _id("stage73-execution-result", result._payload(pre_result, ""))
    result_fp = canonical_sha256(
        result._payload(pre_result, result.execution_result_id)
    )
    pre_evidence = tuple(evidence.canonical_chain[:40])
    evidence_fp = canonical_sha256(
        values(evidence, exclude=("evidence_fingerprint", "canonical_chain"))
        | {"canonical_chain": list(pre_evidence)}
    )
    identity_ok = (
        request.execution_request_id == request_id
        and request.request_fingerprint == request_fp
        and result.execution_result_id == result_id
        and result.result_fingerprint == result_fp
        and evidence.evidence_fingerprint == evidence_fp
    )
    binding_ok = (
        result.request == request
        and request.dispatch_package_id == dispatch_package.dispatch_package_id
        and request.dispatch_fingerprint == dispatch_package.dispatch_fingerprint
        and request.schedule_id == dispatch_package.schedule_id
        and request.queue_record_id == dispatch_package.queue_record_id
        and request.dispatch_key == dispatch_package.dispatch_key
        and request.execution_plan_reference_fingerprint
        == dispatch_package.execution_plan_reference_fingerprint
        and request.work_package_reference_fingerprint
        == dispatch_package.work_package_reference_fingerprint
        and evidence.execution_result_id == result.execution_result_id
        and evidence.execution_result_fingerprint == result.result_fingerprint
    )
    chain_ok = (
        len(request.upstream_chain) == 38
        and tuple(request.upstream_chain) == tuple(dispatch_package.canonical_chain)
        and len(result.canonical_chain) == 40
        and tuple(result.canonical_chain[:38]) == tuple(request.upstream_chain)
        and result.canonical_chain[38] == request.request_fingerprint
        and len(evidence.canonical_chain) == 41
        and tuple(evidence.canonical_chain[:40]) == tuple(result.canonical_chain)
        and len(set(evidence.canonical_chain)) == 41
    )
    scope_ok = request.unit_scope == 1 and evidence.chunk_count == 1
    counts_ok = (
        result.provider_requests == result.provider_attempts
        == result.provider_successes == result.translation_executions == 1
        and result.runtime_executions_started == 1
        and result.controlled_outputs_written == 1
    )
    output_path = Path(artifact_root).resolve() / evidence.output_artifact_path
    try:
        output_path.resolve().relative_to(Path(artifact_root).resolve())
        output_ok = (
            output_path.is_file()
            and hashlib.sha256(output_path.read_bytes()).hexdigest()
            == evidence.output_artifact_fingerprint
            == result.output_artifact_fingerprint
            and len(output_path.read_text(encoding="utf-8"))
            == evidence.output_character_count
            == result.output_character_count
        )
    except (OSError, UnicodeError, ValueError):
        output_ok = False
    quality_ok = (
        result.quality_passed and result.structural_quality_passed
        and result.baseline_quality_passed and evidence.quality_passed
        and not evidence.source_echo_detected
        and not evidence.duplicate_output_detected
        and not evidence.corruption_detected
        and evidence.traditional_chinese_signal
        and evidence.dialogue_punctuation_passed
        and evidence.fixed_names_passed
    )
    state_ok = all(
        getattr(result, name) is True for name in (
            "execution_started", "runtime_executor_invoked",
            "provider_execution_started", "translation_execution_started",
            "output_written",
        )
    )
    zero_ok = all(
        getattr(result, name) == 0 for name in (
            "additional_chunks_started", "retries", "fallbacks",
            "automatic_rollouts", "formal_output_replacements",
            "resume_mutations", "cache_mutations",
        )
    )
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("INVALID_IDENTITY", identity_ok),
        ("BINDING_MISMATCH", binding_ok),
        ("CHAIN_MISMATCH", chain_ok),
        ("SCOPE_MISMATCH", scope_ok),
        ("PROVIDER_COUNT_MISMATCH", counts_ok),
        ("OUTPUT_MISMATCH", output_ok),
        ("QUALITY_FAILED", quality_ok),
        ("STATE_MISMATCH", state_ok),
        ("PROHIBITED_COUNTER", zero_ok),
    )
    reasons = tuple(code for code, passed in checks if not passed)
    verification = ControlledTranslationVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        identity_verified=identity_ok,
        binding_verified=binding_ok,
        chain_verified=chain_ok,
        scope_verified=scope_ok,
        provider_counts_verified=counts_ok,
        output_verified=output_ok,
        quality_verified=quality_ok,
        state_verified=state_ok,
        prohibited_counters_verified=zero_ok,
        reason_codes=reasons,
    )
    if raise_on_error and not verification.valid:
        raise ControlledTranslationVerificationError(",".join(reasons))
    return verification
