"""Atomic Stage 6.13 consumer."""

from __future__ import annotations

from core.controlled_runtime_queue_admission_authorization_consumption import (
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionClaim,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionRequest,
    ControlledRuntimeQueueAdmissionAuthorizationConsumptionResult,
)
from core.controlled_runtime_queue_admission_record import (
    ControlledRuntimeQueueAdmissionRecord,
    ControlledRuntimeQueueAdmissionRecordRequest,
    ControlledRuntimeQueueAdmissionRecordResult,
    verify_controlled_runtime_queue_admission_record,
)

from .errors import (
    QueueAdmissionRecordAlreadyConsumedError,
    QueueAdmissionRecordConsumptionError,
)
from .models import (
    ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    ControlledRuntimeQueueAdmissionRecordConsumptionResult,
)
from .policy import (
    BOUNDARY_KIND,
    CONSUMPTION_INTENT,
    SUCCESS_STATUS,
)
from .registry import ControlledRuntimeQueueAdmissionRecordConsumptionRegistry
from .serialization import canonical_sha256, canonical_json
from .verification import (
    verify_controlled_runtime_queue_admission_record_consumption,
)


class ControlledRuntimeQueueAdmissionRecordConsumer:
    """Deterministic, durable, atomic one-time consumption boundary."""

    def consume(
        self,
        request: ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
        *,
        stage612_record: ControlledRuntimeQueueAdmissionRecord,
        stage612_request: ControlledRuntimeQueueAdmissionRecordRequest,
        stage612_result: ControlledRuntimeQueueAdmissionRecordResult,
        stage612_verification_context: dict[str, object],
        database_path,
        allowed_root,
    ) -> ControlledRuntimeQueueAdmissionRecordConsumptionResult:
        if not isinstance(request, ControlledRuntimeQueueAdmissionRecordConsumptionRequest):
            raise TypeError("request must be Stage 6.13 request")
        if not isinstance(stage612_record, ControlledRuntimeQueueAdmissionRecord):
            raise TypeError("stage612_record must be authentic Stage 6.12 record")
        if not isinstance(stage612_result, ControlledRuntimeQueueAdmissionRecordResult):
            raise TypeError("stage612_result must be authentic Stage 6.12 result")

        stage612_verification = verify_controlled_runtime_queue_admission_record(
            stage612_record,
            request=stage612_request,
            **stage612_verification_context,
        )
        if not stage612_verification.valid:
            return self._denied(
                request,
                ("UPSTREAM_VERIFICATION_FAILED",),
                stage612_verification=stage612_verification,
            )

        if not stage612_result.verification_succeeded:
            return self._denied(
                request,
                ("UPSTREAM_VERIFICATION_FAILED",),
                stage612_verification=stage612_verification,
            )

        if stage612_result.replay_detected:
            return self._denied(
                request,
                ("UPSTREAM_VERIFICATION_FAILED",),
                stage612_verification=stage612_verification,
            )

        if not stage612_result.exactly_one_record_prepared:
            return self._denied(
                request,
                ("RECORD_NOT_PREPARED",),
                stage612_verification=stage612_verification,
            )

        bindings = all((
            request.record_id == stage612_record.queue_admission_record_id,
            request.record_fingerprint == stage612_record.record_fingerprint,
            request.record_request_id == stage612_request.record_request_id,
            request.record_request_fingerprint == stage612_request.request_fingerprint,
            request.consumption_claim_id == stage612_record.consumption_claim_id,
            request.claim_fingerprint == stage612_record.claim_fingerprint,
            request.upstream_consumption_request_id == stage612_record.consumption_request_id,
            request.consumption_request_fingerprint == stage612_record.consumption_request_fingerprint,
            request.authorization_id == stage612_record.authorization_id,
            request.decision_fingerprint == stage612_record.decision_fingerprint,
            request.authorization_request_id == stage612_record.authorization_request_id,
            request.authorization_request_fingerprint == stage612_record.authorization_request_fingerprint,
            request.stage69_claim_fingerprint == stage612_record.stage69_claim_fingerprint,
            request.scheduling_envelope_fingerprint == stage612_record.scheduling_envelope_fingerprint,
            request.stage67_claim_fingerprint == stage612_record.stage67_claim_fingerprint,
            request.stage66_decision_fingerprint == stage612_record.stage66_decision_fingerprint,
            request.runtime_boundary_id == stage612_record.runtime_boundary_id,
            request.runtime_boundary_kind == BOUNDARY_KIND,
            request.selected_adapter_index == stage612_record.selected_adapter_index,
            request.capability_state_fingerprint == stage612_record.capability_state_fingerprint,
            request.admission_class == stage612_record.admission_class,
            request.priority_class == stage612_record.priority_class,
            tuple(request.upstream_chain) == tuple(stage612_record.canonical_chain),
        ))
        if not bindings:
            return self._denied(
                request,
                ("BINDING_MISMATCH",),
                stage612_verification=stage612_verification,
            )

        record_state_ok = all((
            stage612_record.queue_admission_record_prepared,
            not stage612_record.queue_admission_record_consumed,
            not stage612_record.queue_record_created,
            not stage612_record.runtime_execution_scheduled,
            not stage612_record.execution_started,
            stage612_record.scheduling_authorization_consumed,
            stage612_record.scheduling_envelope_prepared,
            stage612_record.scheduling_envelope_consumed,
            not stage612_record.scheduling_envelope_reusable,
            stage612_record.queue_admission_authorized,
            stage612_record.queue_admission_authorization_consumed,
            not stage612_record.queue_admission_authorization_reusable,
        ))
        if not record_state_ok:
            return self._denied(
                request,
                ("UPSTREAM_STATE_MISMATCH",),
                stage612_verification=stage612_verification,
            )

        chain_pre = tuple(stage612_record.canonical_chain) + (request.request_fingerprint,)

        claim = ControlledRuntimeQueueAdmissionRecordConsumptionClaim(
            consumption_request_id=request.consumption_request_id,
            consumption_request_fingerprint=request.request_fingerprint,
            record_id=request.record_id,
            record_fingerprint=request.record_fingerprint,
            record_request_id=request.record_request_id,
            record_request_fingerprint=request.record_request_fingerprint,
            stage611_claim_id=request.consumption_claim_id,
            stage611_claim_fingerprint=request.claim_fingerprint,
            authorization_id=request.authorization_id,
            decision_fingerprint=request.decision_fingerprint,
            authorization_request_id=request.authorization_request_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            stage69_consumption_claim_id=request.stage69_consumption_claim_id,
            stage69_claim_fingerprint=request.stage69_claim_fingerprint,
            scheduling_envelope_id=request.scheduling_envelope_id,
            scheduling_envelope_fingerprint=request.scheduling_envelope_fingerprint,
            stage67_consumption_claim_id=request.stage67_consumption_claim_id,
            stage67_claim_fingerprint=request.stage67_claim_fingerprint,
            stage66_scheduling_authorization_id=request.stage66_scheduling_authorization_id,
            stage66_decision_fingerprint=request.stage66_decision_fingerprint,
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
            selected_adapter_index=request.selected_adapter_index,
            capability_state_fingerprint=request.capability_state_fingerprint,
            unit_scope=request.unit_scope,
            admission_class=request.admission_class,
            priority_class=request.priority_class,
            ordering_key=request.ordering_key,
            scheduling_authorization_consumed=True,
            scheduling_envelope_prepared=True,
            scheduling_envelope_consumed=True,
            scheduling_envelope_reusable=False,
            queue_admission_authorized=True,
            queue_admission_authorization_consumed=True,
            queue_admission_authorization_reusable=False,
            queue_admission_record_prepared=True,
            queue_admission_record_consumed=True,
            queue_admission_record_reusable=False,
            queue_record_created=False,
            runtime_execution_scheduled=False,
            execution_started=False,
            persistent_registry_written=True,
            canonical_chain=chain_pre,
        )

        registry = ControlledRuntimeQueueAdmissionRecordConsumptionRegistry(
            database_path, allowed_root=allowed_root
        )
        try:
            stored = registry.claim(request, claim)
        except QueueAdmissionRecordAlreadyConsumedError:
            return self._denied(
                request,
                ("ALREADY_CONSUMED",),
                replay=True,
                stage612_verification=stage612_verification,
            )
        except QueueAdmissionRecordConsumptionError:
            return self._denied(
                request,
                ("REGISTRY_ERROR",),
                stage612_verification=stage612_verification,
            )

        verification = verify_controlled_runtime_queue_admission_record_consumption(
            stored,
            request=request,
            stage612_record=stage612_record,
            stage612_request=stage612_request,
            stage612_result=stage612_result,
            stage612_verification_context=stage612_verification_context,
            persisted_payload_json=stored.to_json(),
            persistence_committed=True,
        )
        if not verification.valid:
            return self._denied(
                request,
                verification.reason_codes,
                stage612_verification=stage612_verification,
            )

        return ControlledRuntimeQueueAdmissionRecordConsumptionResult(
            request=request,
            claim=stored,
            verification_succeeded=True,
            upstream_verified=True,
            durable_claim_created=True,
            exactly_one_record_consumed=True,
            replay_detected=False,
            persistence_committed=True,
            durable_readback_verified=True,
            status=SUCCESS_STATUS,
            reason_codes=(),
            record_consumption_count=1,
        )

    @staticmethod
    def _denied(
        request,
        reasons,
        *,
        replay=False,
        stage612_verification=None,
    ):
        return ControlledRuntimeQueueAdmissionRecordConsumptionResult(
            request=request,
            claim=None,
            verification_succeeded=False,
            upstream_verified=(
                stage612_verification is not None
                and stage612_verification.valid
            ),
            durable_claim_created=False,
            exactly_one_record_consumed=False,
            replay_detected=replay,
            persistence_committed=False,
            durable_readback_verified=False,
            status="queue_admission_record_consumption_failed",
            reason_codes=tuple(reasons),
            record_consumption_count=0,
        )