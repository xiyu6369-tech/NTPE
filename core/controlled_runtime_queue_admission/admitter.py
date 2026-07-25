"""Controlled Stage 7.1 admission without scheduling or execution."""

from __future__ import annotations

from .errors import (
    ControlledRuntimeQueueAdmissionConflictError,
    ControlledRuntimeQueueAdmissionError,
    ControlledRuntimeQueueAdmissionPolicyError,
    ControlledRuntimeQueueAlreadyAdmittedError,
)
from .models import (
    ControlledRuntimeQueueAdmissionRequest,
    ControlledRuntimeQueueAdmissionResult,
    ControlledRuntimeQueueRecord,
)
from .policy import FAILURE_STATUS, SUCCESS_STATUS
from .registry import ControlledRuntimeQueueRegistry
from .verification import verify_controlled_runtime_queue_record


class ControlledRuntimeQueueAdmitter:
    """Atomically create exactly one durable queue record."""

    def admit(
        self,
        request: ControlledRuntimeQueueAdmissionRequest,
        *,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context: dict[str, object],
        database_path,
        allowed_root,
    ) -> ControlledRuntimeQueueAdmissionResult:
        if not isinstance(request, ControlledRuntimeQueueAdmissionRequest):
            raise TypeError("request must be a Stage 7.1 admission request")

        queue_record = ControlledRuntimeQueueRecord(
            admission_request_id=request.admission_request_id,
            admission_request_fingerprint=request.request_fingerprint,
            stage613_claim_id=request.stage613_claim_id,
            stage613_claim_fingerprint=request.stage613_claim_fingerprint,
            stage613_consumption_request_id=(
                request.stage613_consumption_request_id
            ),
            stage613_consumption_request_fingerprint=(
                request.stage613_consumption_request_fingerprint
            ),
            stage612_record_id=request.stage612_record_id,
            stage612_record_fingerprint=request.stage612_record_fingerprint,
            stage612_preparation_request_id=(
                request.stage612_preparation_request_id
            ),
            stage612_request_fingerprint=request.stage612_request_fingerprint,
            stage611_claim_id=request.stage611_claim_id,
            stage611_claim_fingerprint=request.stage611_claim_fingerprint,
            stage610_authorization_id=request.stage610_authorization_id,
            stage610_decision_fingerprint=(
                request.stage610_decision_fingerprint
            ),
            stage610_authorization_request_id=(
                request.stage610_authorization_request_id
            ),
            stage610_request_fingerprint=request.stage610_request_fingerprint,
            stage69_consumption_claim_id=request.stage69_consumption_claim_id,
            stage69_claim_fingerprint=request.stage69_claim_fingerprint,
            stage68_scheduling_envelope_id=(
                request.stage68_scheduling_envelope_id
            ),
            stage68_envelope_fingerprint=(
                request.stage68_envelope_fingerprint
            ),
            stage67_consumption_claim_id=request.stage67_consumption_claim_id,
            stage67_claim_fingerprint=request.stage67_claim_fingerprint,
            stage66_scheduling_authorization_id=(
                request.stage66_scheduling_authorization_id
            ),
            stage66_decision_fingerprint=(
                request.stage66_decision_fingerprint
            ),
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
            selected_adapter_index=request.selected_adapter_index,
            capability_state_fingerprint=(
                request.capability_state_fingerprint
            ),
            admission_class=request.admission_class,
            priority_class=request.priority_class,
            ordering_key=request.ordering_key,
            unit_scope=request.unit_scope,
            scheduling_authorization_consumed=True,
            scheduling_envelope_prepared=True,
            scheduling_envelope_consumed=True,
            scheduling_envelope_reusable=False,
            queue_admission_authorized=True,
            queue_admission_authorization_consumed=True,
            queue_admission_record_prepared=True,
            queue_admission_record_consumed=True,
            queue_admission_performed=True,
            queue_record_created=True,
            queue_record_consumed=False,
            queue_record_reusable=False,
            runtime_execution_scheduled=False,
            execution_started=False,
            persistent_registry_written=True,
            queue_state=(
                "admitted_pending_controlled_runtime_scheduling"
            ),
            canonical_chain=(
                tuple(request.upstream_chain) + (request.request_fingerprint,)
            ),
        )
        registry = ControlledRuntimeQueueRegistry(
            database_path,
            allowed_root=allowed_root,
        )
        try:
            stored = registry.admit(
                request,
                queue_record,
                stage613_claim=stage613_claim,
                stage613_request=stage613_request,
                stage613_result=stage613_result,
                stage613_verification_context=stage613_verification_context,
            )
        except ControlledRuntimeQueueAlreadyAdmittedError:
            return self._denied(
                request,
                ("ALREADY_ADMITTED",),
                replay=True,
                upstream_verified=True,
            )
        except ControlledRuntimeQueueAdmissionConflictError:
            return self._denied(
                request,
                ("CONFLICT",),
                conflict=True,
                upstream_verified=True,
            )
        except ControlledRuntimeQueueAdmissionPolicyError as error:
            return self._denied(request, error.reason_codes)
        except ControlledRuntimeQueueAdmissionError:
            return self._denied(request, ("REGISTRY_ERROR",))

        verification = verify_controlled_runtime_queue_record(
            stored,
            request=request,
            stage613_claim=stage613_claim,
            stage613_request=stage613_request,
            stage613_result=stage613_result,
            stage613_verification_context=stage613_verification_context,
            persisted_payload_json=stored.to_json(),
            persistence_committed=True,
            durable_readback_verified=True,
        )
        if (
            type(verification.valid) is not bool
            or verification.valid is not True
        ):
            return self._denied(
                request,
                verification.reason_codes,
                persistence_committed=True,
            )
        return ControlledRuntimeQueueAdmissionResult(
            request=request,
            queue_record=stored,
            verification_succeeded=True,
            upstream_verified=True,
            queue_admission_performed=True,
            queue_record_created=True,
            replay_detected=False,
            conflict_detected=False,
            persistence_committed=True,
            durable_readback_verified=True,
            status=SUCCESS_STATUS,
            reason_codes=(),
            queue_admission_count=1,
            queue_record_created_count=1,
        )

    @staticmethod
    def _denied(
        request,
        reason_codes,
        *,
        replay=False,
        conflict=False,
        upstream_verified=False,
        persistence_committed=False,
    ):
        return ControlledRuntimeQueueAdmissionResult(
            request=request,
            queue_record=None,
            verification_succeeded=False,
            upstream_verified=upstream_verified,
            queue_admission_performed=False,
            queue_record_created=False,
            replay_detected=replay,
            conflict_detected=conflict,
            persistence_committed=persistence_committed,
            durable_readback_verified=False,
            status=FAILURE_STATUS,
            reason_codes=tuple(reason_codes),
            queue_admission_count=0,
            queue_record_created_count=0,
        )
