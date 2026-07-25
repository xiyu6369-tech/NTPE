"""Centralized deterministic Stage 7.1 admission policy."""

from __future__ import annotations

from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_request"
REQUEST_SCHEMA_VERSION = "1.0"
QUEUE_RECORD_SCHEMA_NAME = "ntpe.controlled_runtime_queue_record"
QUEUE_RECORD_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_result"
RESULT_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = (
    "ntpe.controlled_runtime_queue_record_verification_result"
)
VERIFICATION_SCHEMA_VERSION = "1.0"
REGISTRY_SCHEMA_NAME = "ntpe.controlled_runtime_queue_registry"
REGISTRY_SCHEMA_VERSION = "1.0"

BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
ADMISSION_CLASS = "controlled_runtime_single_unit"
PRIORITY_CLASS = "controlled_default"
ADMISSION_INTENT = (
    "admit_exactly_one_consumed_and_verified_controlled_runtime_"
    "queue_admission_record_into_the_durable_controlled_runtime_queue"
)
QUEUE_STATE = "admitted_pending_controlled_runtime_scheduling"
SUCCESS_STATUS = "controlled_runtime_queue_record_created_not_scheduled"
FAILURE_STATUS = "controlled_runtime_queue_admission_failed"

REASON_CODES = (
    "INVALID_SCHEMA",
    "INVALID_IDENTITY",
    "FINGERPRINT_MISMATCH",
    "UPSTREAM_VERIFICATION_FAILED",
    "UPSTREAM_RESULT_INVALID",
    "REPLAY_ONLY_AUTHORITY",
    "UPSTREAM_STATE_MISMATCH",
    "BINDING_MISMATCH",
    "INVALID_UNIT_SCOPE",
    "INVALID_INTENT",
    "INVALID_ADMISSION_CLASS",
    "INVALID_PRIORITY_CLASS",
    "INVALID_ORDERING_KEY",
    "CLAIM_NOT_COMMITTED",
    "CLAIM_READBACK_NOT_VERIFIED",
    "CLAIM_NOT_ORIGINAL_SUCCESS",
    "RECORD_NOT_CONSUMED",
    "QUEUE_ALREADY_ADMITTED",
    "QUEUE_RECORD_ALREADY_CREATED",
    "SCHEDULING_ALREADY_STARTED",
    "EXECUTION_ALREADY_STARTED",
    "ACTIVE_CAPABILITY_DETECTED",
    "CHAIN_MISMATCH",
    "CANONICAL_PAYLOAD_MISMATCH",
    "PERSISTENCE_NOT_PROVEN",
    "READBACK_NOT_PROVEN",
    "ALREADY_ADMITTED",
    "CONFLICT",
    "REGISTRY_ERROR",
    "INVARIANT_VIOLATION",
)


def _strict_true(value: object) -> bool:
    return type(value) is bool and value is True


def _strict_false(value: object) -> bool:
    return type(value) is bool and value is False


def _strict_zero(value: object) -> bool:
    return type(value) is int and value == 0


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionPolicy:
    """Offline policy evaluated inside the registry write transaction."""

    unit_scope: int = 1
    upstream_chain_layers: int = 33
    request_chain_layers: int = 34
    complete_chain_layers: int = 35
    runtime_boundary_kind: str = BOUNDARY_KIND
    admission_intent: str = ADMISSION_INTENT
    admission_class: str = ADMISSION_CLASS
    priority_class: str = PRIORITY_CLASS
    queue_state: str = QUEUE_STATE

    def evaluate(
        self,
        request,
        *,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context,
    ) -> tuple[str, ...]:
        """Return deterministic denials; programming/type errors remain visible."""

        from core.controlled_runtime_queue_admission_record_consumption import (
            ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
            ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
            ControlledRuntimeQueueAdmissionRecordConsumptionResult,
            ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult,
            verify_controlled_runtime_queue_admission_record_consumption,
        )
        from core.controlled_runtime_queue_admission_record_consumption.policy import (
            RESULT_SCHEMA_NAME as STAGE613_RESULT_SCHEMA_NAME,
            RESULT_SCHEMA_VERSION as STAGE613_RESULT_SCHEMA_VERSION,
            SUCCESS_STATUS as STAGE613_SUCCESS_STATUS,
        )

        from .models import ControlledRuntimeQueueAdmissionRequest, _id
        from .serialization import canonical_sha256, values

        if not isinstance(request, ControlledRuntimeQueueAdmissionRequest):
            raise TypeError("request must be a Stage 7.1 admission request")
        if not isinstance(
            stage613_claim,
            ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
        ):
            raise TypeError("stage613_claim must be an authentic Stage 6.13 claim")
        if not isinstance(
            stage613_request,
            ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
        ):
            raise TypeError(
                "stage613_request must be an authentic Stage 6.13 request"
            )
        if not isinstance(
            stage613_result,
            ControlledRuntimeQueueAdmissionRecordConsumptionResult,
        ):
            raise TypeError(
                "stage613_result must be an authentic Stage 6.13 result"
            )
        if not isinstance(stage613_verification_context, dict):
            raise TypeError("stage613_verification_context must be a dict")

        upstream = verify_controlled_runtime_queue_admission_record_consumption(
            stage613_claim,
            request=stage613_request,
            persisted_payload_json=stage613_claim.to_json(),
            persistence_committed=True,
            **stage613_verification_context,
        )
        if not isinstance(
            upstream,
            ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult,
        ):
            raise TypeError("Stage 6.13 verifier returned an invalid result type")

        request_id = _id(
            "stage71-queue-admission-request",
            values(
                request,
                exclude=("admission_request_id", "request_fingerprint"),
            ),
        )
        request_fingerprint = canonical_sha256(
            values(request, exclude=("request_fingerprint",))
        )
        schema_ok = (
            request.schema_name,
            request.schema_version,
        ) == (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION)
        identity_ok = request.admission_request_id == request_id
        fingerprint_ok = request.request_fingerprint == request_fingerprint

        original_success = all(
            (
                stage613_result.request == stage613_request,
                stage613_result.claim == stage613_claim,
                (stage613_result.schema_name, stage613_result.schema_version)
                == (STAGE613_RESULT_SCHEMA_NAME, STAGE613_RESULT_SCHEMA_VERSION),
                stage613_result.status == STAGE613_SUCCESS_STATUS,
                stage613_result.reason_codes == (),
                _strict_true(stage613_result.verification_succeeded),
                _strict_true(stage613_result.upstream_verified),
                _strict_true(stage613_result.durable_claim_created),
                _strict_true(stage613_result.exactly_one_record_consumed),
                _strict_false(stage613_result.replay_detected),
                _strict_true(stage613_result.persistence_committed),
                _strict_true(stage613_result.durable_readback_verified),
                type(stage613_result.record_consumption_count) is int
                and stage613_result.record_consumption_count == 1,
            )
        )
        inactive_counts = all(
            _strict_zero(getattr(stage613_result, name))
            for name in (
                "queue_admission_count",
                "queue_record_created_count",
                "queue_record_consumed_count",
                "scheduling_queued_count",
                "scheduler_count",
                "runtime_execution_count",
                "provider_execution_count",
                "network_execution_count",
                "translation_execution_count",
            )
        )
        upstream_ok = upstream.valid is True

        bindings = all(
            (
                request.stage613_claim_id
                == stage613_claim.consumption_claim_id,
                request.stage613_claim_fingerprint
                == stage613_claim.claim_fingerprint,
                request.stage613_consumption_request_id
                == stage613_claim.consumption_request_id,
                request.stage613_consumption_request_fingerprint
                == stage613_claim.consumption_request_fingerprint,
                request.stage612_record_id == stage613_claim.record_id,
                request.stage612_record_fingerprint
                == stage613_claim.record_fingerprint,
                request.stage612_preparation_request_id
                == stage613_claim.record_request_id,
                request.stage612_request_fingerprint
                == stage613_claim.record_request_fingerprint,
                request.stage611_claim_id == stage613_claim.stage611_claim_id,
                request.stage611_claim_fingerprint
                == stage613_claim.stage611_claim_fingerprint,
                request.stage610_authorization_id
                == stage613_claim.authorization_id,
                request.stage610_decision_fingerprint
                == stage613_claim.decision_fingerprint,
                request.stage610_authorization_request_id
                == stage613_claim.authorization_request_id,
                request.stage610_request_fingerprint
                == stage613_claim.authorization_request_fingerprint,
                request.stage69_consumption_claim_id
                == stage613_claim.stage69_consumption_claim_id,
                request.stage69_claim_fingerprint
                == stage613_claim.stage69_claim_fingerprint,
                request.stage68_scheduling_envelope_id
                == stage613_claim.scheduling_envelope_id,
                request.stage68_envelope_fingerprint
                == stage613_claim.scheduling_envelope_fingerprint,
                request.stage67_consumption_claim_id
                == stage613_claim.stage67_consumption_claim_id,
                request.stage67_claim_fingerprint
                == stage613_claim.stage67_claim_fingerprint,
                request.stage66_scheduling_authorization_id
                == stage613_claim.stage66_scheduling_authorization_id,
                request.stage66_decision_fingerprint
                == stage613_claim.stage66_decision_fingerprint,
                request.runtime_boundary_id
                == stage613_claim.runtime_boundary_id,
                request.runtime_boundary_kind
                == stage613_claim.runtime_boundary_kind,
                request.selected_adapter_index
                == stage613_claim.selected_adapter_index,
                request.capability_state_fingerprint
                == stage613_claim.capability_state_fingerprint,
                request.admission_class == stage613_claim.admission_class,
                request.priority_class == stage613_claim.priority_class,
                request.ordering_key == stage613_claim.ordering_key,
                request.unit_scope == stage613_claim.unit_scope,
            )
        )
        chain_ok = all(
            (
                len(stage613_claim.canonical_chain)
                == self.upstream_chain_layers,
                tuple(request.upstream_chain)
                == tuple(stage613_claim.canonical_chain),
                len(set(request.upstream_chain))
                == self.upstream_chain_layers,
                request.upstream_chain[-1]
                == stage613_claim.claim_fingerprint,
            )
        )
        inherited_state = all(
            (
                _strict_true(stage613_claim.scheduling_authorization_consumed),
                _strict_true(stage613_claim.scheduling_envelope_prepared),
                _strict_true(stage613_claim.scheduling_envelope_consumed),
                _strict_false(stage613_claim.scheduling_envelope_reusable),
                _strict_true(stage613_claim.queue_admission_authorized),
                _strict_true(
                    stage613_claim.queue_admission_authorization_consumed
                ),
                _strict_false(
                    stage613_claim.queue_admission_authorization_reusable
                ),
                _strict_true(stage613_claim.queue_admission_record_prepared),
                _strict_true(stage613_claim.queue_admission_record_consumed),
                _strict_false(stage613_claim.queue_admission_record_reusable),
                _strict_false(stage613_claim.queue_record_created),
                _strict_false(stage613_claim.runtime_execution_scheduled),
                _strict_false(stage613_claim.execution_started),
                _strict_true(stage613_claim.persistent_registry_written),
            )
        )

        checks = (
            ("INVALID_SCHEMA", schema_ok),
            ("INVALID_IDENTITY", identity_ok),
            ("FINGERPRINT_MISMATCH", fingerprint_ok),
            ("UPSTREAM_VERIFICATION_FAILED", upstream_ok),
            ("UPSTREAM_RESULT_INVALID", original_success),
            (
                "REPLAY_ONLY_AUTHORITY",
                _strict_false(stage613_result.replay_detected),
            ),
            (
                "CLAIM_NOT_COMMITTED",
                _strict_true(stage613_result.persistence_committed),
            ),
            (
                "CLAIM_READBACK_NOT_VERIFIED",
                _strict_true(stage613_result.durable_readback_verified),
            ),
            ("BINDING_MISMATCH", bindings),
            (
                "INVALID_UNIT_SCOPE",
                type(request.unit_scope) is int and request.unit_scope == 1,
            ),
            ("INVALID_INTENT", request.admission_intent == ADMISSION_INTENT),
            (
                "INVALID_ADMISSION_CLASS",
                request.admission_class == ADMISSION_CLASS,
            ),
            (
                "INVALID_PRIORITY_CLASS",
                request.priority_class == PRIORITY_CLASS,
            ),
            (
                "INVALID_ORDERING_KEY",
                request.ordering_key == stage613_claim.ordering_key,
            ),
            ("CHAIN_MISMATCH", chain_ok),
            ("UPSTREAM_STATE_MISMATCH", inherited_state),
            (
                "RECORD_NOT_CONSUMED",
                _strict_true(stage613_claim.queue_admission_record_consumed),
            ),
            (
                "QUEUE_RECORD_ALREADY_CREATED",
                _strict_false(stage613_claim.queue_record_created),
            ),
            (
                "SCHEDULING_ALREADY_STARTED",
                _strict_false(stage613_claim.runtime_execution_scheduled),
            ),
            (
                "EXECUTION_ALREADY_STARTED",
                _strict_false(stage613_claim.execution_started),
            ),
            ("ACTIVE_CAPABILITY_DETECTED", inactive_counts),
        )
        return tuple(code for code, valid in checks if not valid)
