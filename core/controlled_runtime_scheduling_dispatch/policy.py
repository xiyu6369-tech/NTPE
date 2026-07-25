"""Central deterministic offline policy for Stage 7.2."""

from __future__ import annotations

from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_request"
REQUEST_SCHEMA_VERSION = "1.0"
SCHEDULE_SCHEMA_NAME = "ntpe.controlled_runtime_execution_schedule"
SCHEDULE_SCHEMA_VERSION = "1.0"
DISPATCH_SCHEMA_NAME = "ntpe.controlled_runtime_dispatch_package"
DISPATCH_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_result"
RESULT_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = (
    "ntpe.controlled_runtime_scheduling_dispatch_verification_result"
)
VERIFICATION_SCHEMA_VERSION = "1.0"
REGISTRY_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_registry"
REGISTRY_SCHEMA_VERSION = "1.0"

BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
ADMISSION_CLASS = "controlled_runtime_single_unit"
PRIORITY_CLASS = "controlled_default"
SCHEDULING_INTENT = (
    "consume_exactly_one_authentic_durable_runtime_queue_record_create_"
    "exactly_one_durable_execution_schedule_and_prepare_exactly_one_"
    "immutable_dispatch_package"
)
SCHEDULE_STATE = "scheduled_pending_runtime_executor_invocation"
SUCCESS_STATUS = "controlled_runtime_scheduled_dispatch_prepared_not_executed"
FAILURE_STATUS = "controlled_runtime_scheduling_dispatch_failed"

REASON_CODES = (
    "INVALID_SCHEMA",
    "INVALID_IDENTITY",
    "FINGERPRINT_MISMATCH",
    "UPSTREAM_VERIFICATION_FAILED",
    "UPSTREAM_RESULT_INVALID",
    "REPLAY_ONLY_AUTHORITY",
    "BINDING_MISMATCH",
    "INVALID_UNIT_SCOPE",
    "INVALID_INTENT",
    "INVALID_ADMISSION_CLASS",
    "INVALID_PRIORITY_CLASS",
    "INVALID_ORDERING_KEY",
    "INVALID_DISPATCH_KEY",
    "QUEUE_NOT_ADMITTED",
    "QUEUE_RECORD_NOT_CREATED",
    "QUEUE_ALREADY_CONSUMED",
    "QUEUE_RECORD_REUSABLE",
    "SCHEDULING_ALREADY_STARTED",
    "EXECUTION_ALREADY_STARTED",
    "ACTIVE_CAPABILITY_DETECTED",
    "CHAIN_MISMATCH",
    "CANONICAL_PAYLOAD_MISMATCH",
    "PERSISTENCE_NOT_PROVEN",
    "SCHEDULE_READBACK_NOT_PROVEN",
    "DISPATCH_READBACK_NOT_PROVEN",
    "ALREADY_SCHEDULED",
    "CONFLICT",
    "REGISTRY_ERROR",
    "INVARIANT_VIOLATION",
)


@dataclass(frozen=True)
class ControlledRuntimeSchedulingPolicy:
    unit_scope: int = 1
    upstream_chain_layers: int = 35
    request_chain_layers: int = 36
    schedule_chain_layers: int = 37
    dispatch_chain_layers: int = 38
    runtime_boundary_kind: str = BOUNDARY_KIND
    scheduling_intent: str = SCHEDULING_INTENT
    admission_class: str = ADMISSION_CLASS
    priority_class: str = PRIORITY_CLASS
    schedule_state: str = SCHEDULE_STATE

    def evaluate(
        self,
        request,
        *,
        queue_record,
        stage71_request,
        stage71_result,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context,
    ) -> tuple[str, ...]:
        from core.controlled_runtime_queue_admission import (
            ControlledRuntimeQueueAdmissionResult,
            ControlledRuntimeQueueRecord,
            verify_controlled_runtime_queue_record,
        )
        from core.controlled_runtime_queue_admission.policy import (
            SUCCESS_STATUS as STAGE71_SUCCESS_STATUS,
        )

        reasons: list[str] = []
        if not isinstance(queue_record, ControlledRuntimeQueueRecord):
            return ("UPSTREAM_RESULT_INVALID",)
        if not isinstance(stage71_result, ControlledRuntimeQueueAdmissionResult):
            return ("UPSTREAM_RESULT_INVALID",)
        verification = verify_controlled_runtime_queue_record(
            queue_record,
            request=stage71_request,
            stage613_claim=stage613_claim,
            stage613_request=stage613_request,
            stage613_result=stage613_result,
            stage613_verification_context=stage613_verification_context,
            persisted_payload_json=queue_record.to_json(),
            persistence_committed=True,
            durable_readback_verified=True,
        )
        if type(verification.valid) is not bool or verification.valid is not True:
            reasons.append("UPSTREAM_VERIFICATION_FAILED")
        if not all(
            (
                stage71_result.status == STAGE71_SUCCESS_STATUS,
                stage71_result.queue_record == queue_record,
                stage71_result.request == stage71_request,
                stage71_result.verification_succeeded is True,
                stage71_result.queue_admission_performed is True,
                stage71_result.queue_record_created is True,
                stage71_result.replay_detected is False,
                stage71_result.conflict_detected is False,
                stage71_result.persistence_committed is True,
                stage71_result.durable_readback_verified is True,
            )
        ):
            reasons.append("REPLAY_ONLY_AUTHORITY")
        bindings = (
            ("queue_record_id", queue_record.queue_record_id),
            ("queue_record_fingerprint", queue_record.queue_record_fingerprint),
            ("admission_request_id", queue_record.admission_request_id),
            (
                "admission_request_fingerprint",
                queue_record.admission_request_fingerprint,
            ),
            ("stage613_claim_id", queue_record.stage613_claim_id),
            ("stage613_claim_fingerprint", queue_record.stage613_claim_fingerprint),
            ("stage612_record_id", queue_record.stage612_record_id),
            ("stage612_record_fingerprint", queue_record.stage612_record_fingerprint),
            ("stage611_claim_id", queue_record.stage611_claim_id),
            ("stage611_claim_fingerprint", queue_record.stage611_claim_fingerprint),
            ("stage610_authorization_id", queue_record.stage610_authorization_id),
            (
                "stage610_decision_fingerprint",
                queue_record.stage610_decision_fingerprint,
            ),
            ("stage69_consumption_claim_id", queue_record.stage69_consumption_claim_id),
            ("stage69_claim_fingerprint", queue_record.stage69_claim_fingerprint),
            (
                "stage68_scheduling_envelope_id",
                queue_record.stage68_scheduling_envelope_id,
            ),
            ("stage68_envelope_fingerprint", queue_record.stage68_envelope_fingerprint),
            (
                "stage67_consumption_claim_id",
                queue_record.stage67_consumption_claim_id,
            ),
            ("stage67_claim_fingerprint", queue_record.stage67_claim_fingerprint),
            (
                "stage66_scheduling_authorization_id",
                queue_record.stage66_scheduling_authorization_id,
            ),
            ("stage66_decision_fingerprint", queue_record.stage66_decision_fingerprint),
            ("runtime_boundary_id", queue_record.runtime_boundary_id),
            ("runtime_boundary_kind", queue_record.runtime_boundary_kind),
            ("selected_adapter_index", queue_record.selected_adapter_index),
            (
                "capability_state_fingerprint",
                queue_record.capability_state_fingerprint,
            ),
            ("admission_class", queue_record.admission_class),
            ("priority_class", queue_record.priority_class),
            ("ordering_key", queue_record.ordering_key),
            ("unit_scope", queue_record.unit_scope),
        )
        if not all(getattr(request, name, None) == expected for name, expected in bindings):
            reasons.append("BINDING_MISMATCH")
        if request.execution_plan_reference_fingerprint != queue_record.canonical_chain[6]:
            reasons.append("BINDING_MISMATCH")
        if request.work_package_reference_fingerprint != queue_record.canonical_chain[0]:
            reasons.append("BINDING_MISMATCH")
        state_checks = (
            ("QUEUE_NOT_ADMITTED", queue_record.queue_admission_performed is True),
            ("QUEUE_RECORD_NOT_CREATED", queue_record.queue_record_created is True),
            ("QUEUE_ALREADY_CONSUMED", queue_record.queue_record_consumed is False),
            ("QUEUE_RECORD_REUSABLE", queue_record.queue_record_reusable is False),
            (
                "SCHEDULING_ALREADY_STARTED",
                queue_record.runtime_execution_scheduled is False,
            ),
            ("EXECUTION_ALREADY_STARTED", queue_record.execution_started is False),
        )
        reasons.extend(code for code, valid in state_checks if not valid)
        if request.scheduling_intent != SCHEDULING_INTENT:
            reasons.append("INVALID_INTENT")
        if type(request.unit_scope) is not int or request.unit_scope != 1:
            reasons.append("INVALID_UNIT_SCOPE")
        if request.admission_class != ADMISSION_CLASS:
            reasons.append("INVALID_ADMISSION_CLASS")
        if request.priority_class != PRIORITY_CLASS:
            reasons.append("INVALID_PRIORITY_CLASS")
        if request.ordering_key != queue_record.ordering_key:
            reasons.append("INVALID_ORDERING_KEY")
        if tuple(request.upstream_chain) != tuple(queue_record.canonical_chain):
            reasons.append("CHAIN_MISMATCH")
        return tuple(dict.fromkeys(reasons))
