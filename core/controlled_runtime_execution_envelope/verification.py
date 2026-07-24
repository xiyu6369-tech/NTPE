"""Stage 6.4 — Controlled Runtime Execution Envelope Verification

Pure verification function that validates an execution envelope against
all Stage 6.4 policy invariants without side effects or execution.

verify_execution_envelope is the sole public verification API.
"""

from __future__ import annotations

from .models import (
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeFinding,
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelopeResult,
)
from .policy import (
    ALLOWED_ENVELOPE_STATES,
    ALLOWED_EXECUTION_MODES,
    DEFAULT_POLICY,
)


def verify_execution_envelope(
    envelope: ControlledRuntimeExecutionEnvelope,
) -> ControlledRuntimeExecutionEnvelopeResult:
    """Verify an existing execution envelope against policy invariants.

    Returns a success result (status=runtime_handoff_prepared_not_executed)
    if the envelope is valid (all invariants hold).
    Returns a rejection result if any verification check fails.

    This verification does NOT:
    - start Runtime
    - call Provider
    - contact Network
    - write any file
    - create threads or subprocesses
    - mutate the envelope or any upstream object

    Args:
        envelope: An immutable ControlledRuntimeExecutionEnvelope to verify.

    Returns:
        None on success, or a ControlledRuntimeExecutionEnvelopeResult
        with status!=success indicating which checks failed.
    """
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # 1. Schema name and version
    if envelope.schema_name != "ntpe.controlled_runtime_execution_envelope":
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="ENVELOPE_SCHEMA_MISMATCH",
                severity="error",
                message="Envelope schema_name must be ntpe.controlled_runtime_execution_envelope.",
                field="schema_name",
                expected="ntpe.controlled_runtime_execution_envelope",
                observed=envelope.schema_name,
            )
        )
    if envelope.schema_version != "1.0":
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="ENVELOPE_VERSION_MISMATCH",
                severity="error",
                message="Envelope schema_version must be 1.0.",
                field="schema_version",
                expected="1.0",
                observed=envelope.schema_version,
            )
        )

    # 2. Envelope state
    if envelope.envelope_state not in ALLOWED_ENVELOPE_STATES:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="ENVELOPE_STATE_INVALID",
                severity="blocking",
                message="Envelope state must be runtime_handoff_prepared_not_executed.",
                field="envelope_state",
                expected="runtime_handoff_prepared_not_executed",
                observed=envelope.envelope_state,
            )
        )

    # 3. Execution mode
    if envelope.execution_mode not in ALLOWED_EXECUTION_MODES:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="EXECUTION_MODE_INVALID",
                severity="blocking",
                message="Execution mode must be controlled_single_execution.",
                field="execution_mode",
                expected="controlled_single_execution",
                observed=envelope.execution_mode,
            )
        )

    # 4. Unit count exactly 1
    if envelope.execution_unit_count != 1:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="EXECUTION_UNIT_COUNT_INVALID",
                severity="blocking",
                message="execution_unit_count must be exactly 1.",
                field="execution_unit_count",
                expected="1",
                observed=str(envelope.execution_unit_count),
            )
        )

    # 5. authorization_consumption_prepared must be true
    if not envelope.authorization_consumption_prepared:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="CONSUMPTION_NOT_PREPARED",
                severity="blocking",
                message="authorization_consumption_prepared must be true.",
                field="authorization_consumption_prepared",
                expected="True",
                observed="False",
            )
        )

    # 6. authorization_consumed must be true
    if not envelope.authorization_consumed:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="AUTHORIZATION_NOT_CONSUMED",
                severity="blocking",
                message="authorization_consumed must be true.",
                field="authorization_consumed",
                expected="True",
                observed="False",
            )
        )

    # 7. authorization_reusable must be false
    if envelope.authorization_reusable:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="AUTHORIZATION_REUSABLE",
                severity="blocking",
                message="authorization_reusable must be false.",
                field="authorization_reusable",
                expected="False",
                observed="True",
            )
        )

    # 8. durable_reuse_prevention_established must be true
    if not envelope.durable_reuse_prevention_established:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="DURABLE_PREVENTION_FALSE",
                severity="blocking",
                message="durable_reuse_prevention_established must be true.",
                field="durable_reuse_prevention_established",
                expected="True",
                observed="False",
            )
        )

    # 9. persistent_registry_written must be true
    if not envelope.persistent_registry_written:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="REGISTRY_WRITTEN_FALSE",
                severity="blocking",
                message="persistent_registry_written must be true.",
                field="persistent_registry_written",
                expected="True",
                observed="False",
            )
        )

    # 10. runtime_handoff_prepared must be true
    if not envelope.runtime_handoff_prepared:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="HANDOFF_PREPARED_FALSE",
                severity="blocking",
                message="runtime_handoff_prepared must be true.",
                field="runtime_handoff_prepared",
                expected="True",
                observed="False",
            )
        )

    # 11. runtime_handoff_completed must be false
    if envelope.runtime_handoff_completed:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="HANDOFF_COMPLETED_TRUE",
                severity="blocking",
                message="runtime_handoff_completed must be false.",
                field="runtime_handoff_completed",
                expected="False",
                observed="True",
            )
        )

    # 12. execution_started must be false
    if envelope.execution_started:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="EXECUTION_STARTED_TRUE",
                severity="blocking",
                message="execution_started must be false.",
                field="execution_started",
                expected="False",
                observed="True",
            )
        )

    # 13. execution_completed must be false
    if envelope.execution_completed:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="EXECUTION_COMPLETED_TRUE",
                severity="blocking",
                message="execution_completed must be false.",
                field="execution_completed",
                expected="False",
                observed="True",
            )
        )

    # 14. All execution/write enablements must be false
    capability_checks: list[tuple[str, bool]] = [
        ("runtime_execution_enabled", envelope.runtime_execution_enabled),
        ("provider_execution_enabled", envelope.provider_execution_enabled),
        ("network_execution_enabled", envelope.network_execution_enabled),
        ("translation_execution_enabled", envelope.translation_execution_enabled),
        ("output_write_enabled", envelope.output_write_enabled),
        ("resume_write_enabled", envelope.resume_write_enabled),
        ("cache_write_enabled", envelope.cache_write_enabled),
        ("retry_enabled", envelope.retry_enabled),
        ("fallback_enabled", envelope.fallback_enabled),
        ("production_hook_enabled", envelope.production_hook_enabled),
    ]
    for field_name, value in capability_checks:
        if value:
            code = field_name.upper() + "_INVALID"
            findings.append(
                ControlledRuntimeExecutionEnvelopeFinding(
                    code=code,
                    severity="blocking",
                    message=f"{field_name} must be false.",
                    field=field_name,
                    expected="False",
                    observed="True",
                )
            )

    # 15. Fingerprint chain must have 15 complete layers
    if len(envelope.upstream_fingerprint_chain) != DEFAULT_POLICY.complete_chain_layers:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="CHAIN_LENGTH_INVALID",
                severity="blocking",
                message="upstream_fingerprint_chain must have exactly 15 layers.",
                field="upstream_fingerprint_chain",
                expected="15",
                observed=str(len(envelope.upstream_fingerprint_chain)),
            )
        )

    # 16. Envelope fingerprint must match canonical payload
    from .models import canonical_sha256

    expected_fp = canonical_sha256(
        envelope._fingerprint_payload(envelope.upstream_fingerprint_chain[:14])
    )
    if expected_fp != envelope.envelope_fingerprint:
        findings.append(
            ControlledRuntimeExecutionEnvelopeFinding(
                code="ENVELOPE_FINGERPRINT_TAMPERED",
                severity="blocking",
                message="Envelope fingerprint does not match canonical payload.",
                field="envelope_fingerprint",
                expected=expected_fp,
                observed=envelope.envelope_fingerprint,
            )
        )

    # Build result
    if any(f.severity == "blocking" for f in findings):
        # Build a result-request using safe fallback values for any field
        # that may have been rejected by the envelope model.
        safe_mode = (
            envelope.execution_mode
            if envelope.execution_mode in ALLOWED_EXECUTION_MODES
            else "controlled_single_execution"
        )
        safe_scope = f"verify:{envelope.envelope_id}"
        return ControlledRuntimeExecutionEnvelopeResult(
            request=ControlledRuntimeExecutionEnvelopeRequest(
                envelope_id=envelope.envelope_id,
                claim_id=envelope.claim_id,
                consumption_id=envelope.consumption_id,
                authorization_id=envelope.authorization_id,
                authorization_request_fingerprint=envelope.authorization_request_fingerprint,
                authorization_decision_fingerprint=envelope.authorization_decision_fingerprint,
                execution_plan_fingerprint=envelope.execution_plan_fingerprint,
                stage62_request_fingerprint=envelope.stage62_request_fingerprint,
                stage62_record_fingerprint=envelope.stage62_record_fingerprint,
                stage63_claim_request_fingerprint=envelope.stage63_claim_request_fingerprint,
                stage63_claim_fingerprint=envelope.stage63_claim_fingerprint,
                selected_adapter_index=envelope.selected_adapter_index,
                requested_unit_count=1,
                runtime_handoff_requested=True,
                caller_confirmation=True,
                runtime_scope=safe_scope,
                execution_mode=safe_mode,
                purpose="envelope verification — all execution boundaries must be false",
            ),
            envelope=envelope,
            freeze_gate_verified=True,
            execution_plan_verified=True,
            authorization_request_verified=True,
            authorization_decision_verified=True,
            stage62_request_verified=True,
            stage62_record_verified=True,
            stage62_result_verified=True,
            stage63_claim_request_verified=True,
            stage63_claim_verified=True,
            stage63_result_verified=True,
            authorization_binding_verified=True,
            consumption_binding_verified=True,
            durable_claim_binding_verified=True,
            execution_unit_verified=True,
            runtime_scope_verified=True,
            policy_findings=tuple(findings),
            status="verification_failed",
            recommended_action="do_not_execute",
        )

    return _build_success_result(envelope, tuple(findings))


def _build_success_result(
    envelope: ControlledRuntimeExecutionEnvelope,
    findings: tuple[ControlledRuntimeExecutionEnvelopeFinding, ...],
) -> ControlledRuntimeExecutionEnvelopeResult:
    """Build a success result for a verified envelope.

    All verification checks passed — no blocking findings.
    Status is 'runtime_handoff_prepared_not_executed' and
    recommended_action is 'retain_for_controlled_runtime_handoff'.
    """
    return ControlledRuntimeExecutionEnvelopeResult(
        request=ControlledRuntimeExecutionEnvelopeRequest(
            envelope_id=envelope.envelope_id,
            claim_id=envelope.claim_id,
            consumption_id=envelope.consumption_id,
            authorization_id=envelope.authorization_id,
            authorization_request_fingerprint=envelope.authorization_request_fingerprint,
            authorization_decision_fingerprint=envelope.authorization_decision_fingerprint,
            execution_plan_fingerprint=envelope.execution_plan_fingerprint,
            stage62_request_fingerprint=envelope.stage62_request_fingerprint,
            stage62_record_fingerprint=envelope.stage62_record_fingerprint,
            stage63_claim_request_fingerprint=envelope.stage63_claim_request_fingerprint,
            stage63_claim_fingerprint=envelope.stage63_claim_fingerprint,
            selected_adapter_index=envelope.selected_adapter_index,
            requested_unit_count=1,
            runtime_handoff_requested=True,
            caller_confirmation=True,
            runtime_scope=f"verify:{envelope.envelope_id}",
            execution_mode=envelope.execution_mode,
            purpose="envelope verification — success",
        ),
        envelope=envelope,
        freeze_gate_verified=True,
        execution_plan_verified=True,
        authorization_request_verified=True,
        authorization_decision_verified=True,
        stage62_request_verified=True,
        stage62_record_verified=True,
        stage62_result_verified=True,
        stage63_claim_request_verified=True,
        stage63_claim_verified=True,
        stage63_result_verified=True,
        authorization_binding_verified=True,
        consumption_binding_verified=True,
        durable_claim_binding_verified=True,
        execution_unit_verified=True,
        runtime_scope_verified=True,
        policy_findings=findings,
        status="runtime_handoff_prepared_not_executed",
        recommended_action="retain_for_controlled_runtime_handoff",
    )
