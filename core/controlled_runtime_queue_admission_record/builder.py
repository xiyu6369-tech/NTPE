"""Stateless Stage 6.12 queue-admission record builder."""

from __future__ import annotations

from core.controlled_runtime_queue_admission_authorization_consumption import (
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
)

from .models import (
    ControlledRuntimeQueueAdmissionRecord,
    ControlledRuntimeQueueAdmissionRecordRequest,
    ControlledRuntimeQueueAdmissionRecordResult,
)
from .policy import PREPARATION_INTENT, SUCCESS_STATUS
from .verification import verify_controlled_runtime_queue_admission_record


class ControlledRuntimeQueueAdmissionRecordBuilder:
    """Pure offline record preparation boundary."""

    def prepare(
        self,
        request: ControlledRuntimeQueueAdmissionRecordRequest,
        *,
        stage611_claim: ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
        stage611_request: ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
        stage611_result: ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
        stage611_verification_context: dict[str, object],
    ) -> ControlledRuntimeQueueAdmissionRecordResult:
        if not isinstance(request, ControlledRuntimeQueueAdmissionRecordRequest):
            raise TypeError("request must be Stage 6.12 request")
        try:
            record = ControlledRuntimeQueueAdmissionRecord(
                record_request_id=request.record_request_id,
                record_request_fingerprint=request.request_fingerprint,
                **{n: getattr(request, n) for n in (
                    "consumption_claim_id", "claim_fingerprint",
                    "consumption_request_id", "consumption_request_fingerprint",
                    "authorization_id", "decision_fingerprint",
                    "authorization_request_id", "authorization_request_fingerprint",
                    "stage69_consumption_claim_id", "stage69_claim_fingerprint",
                    "scheduling_envelope_id", "scheduling_envelope_fingerprint",
                    "stage67_consumption_claim_id", "stage67_claim_fingerprint",
                    "stage66_scheduling_authorization_id", "stage66_decision_fingerprint",
                    "runtime_boundary_id", "runtime_boundary_kind",
                    "selected_adapter_index", "capability_state_fingerprint",
                    "unit_scope", "admission_class", "priority_class",
                )},
                scheduling_authorization_consumed=True,
                scheduling_envelope_prepared=True,
                scheduling_envelope_consumed=True,
                scheduling_envelope_reusable=False,
                queue_admission_authorized=True,
                queue_admission_authorization_consumed=True,
                queue_admission_authorization_reusable=False,
                queue_admission_record_prepared=True,
                queue_admission_record_consumed=False,
                queue_record_created=False,
                runtime_execution_scheduled=False,
                execution_started=False,
                persistent_registry_written=True,
                canonical_chain=tuple(request.upstream_chain) + (request.request_fingerprint,),
            )
            verification = verify_controlled_runtime_queue_admission_record(
                record,
                request=request,
                stage611_claim=stage611_claim,
                stage611_request=stage611_request,
                stage611_result=stage611_result,
                stage611_verification_context=stage611_verification_context,
            )
        except (TypeError, ValueError):
            return self._denied(request, ("INVARIANT_VIOLATION",))
        if not verification.valid:
            return self._denied(request, verification.reason_codes)
        return ControlledRuntimeQueueAdmissionRecordResult(
            request=request, record=record,
            verification_succeeded=True, upstream_verified=True,
            durable_record_created=False, exactly_one_record_prepared=True,
            replay_detected=False, persistence_committed=False,
            durable_readback_verified=False,
            status=SUCCESS_STATUS, reason_codes=(),
            record_preparation_count=1,
        )

    @staticmethod
    def _denied(request, reasons):
        return ControlledRuntimeQueueAdmissionRecordResult(
            request=request, record=None,
            verification_succeeded=False, upstream_verified=False,
            durable_record_created=False, exactly_one_record_prepared=False,
            replay_detected=False, persistence_committed=False,
            durable_readback_verified=False,
            status="queue_admission_record_preparation_failed",
            reason_codes=tuple(reasons), record_preparation_count=0,
        )
