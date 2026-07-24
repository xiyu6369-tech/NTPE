"""Stateless Stage 6.10 queue-admission authorizer."""

from __future__ import annotations

from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    ControlledRuntimeSchedulingEnvelopeConsumptionResult,
)

from .models import (
    ControlledRuntimeQueueAdmissionAuthorizationDecision,
    ControlledRuntimeQueueAdmissionAuthorizationRequest,
    ControlledRuntimeQueueAdmissionAuthorizationResult,
)
from .policy import AUTHORIZED_STATUS, DENIED_STATUS
from .verification import verify_controlled_runtime_queue_admission_authorization


class ControlledRuntimeQueueAdmissionAuthorizer:
    """Pure offline authorization boundary."""

    def authorize(
        self,
        request: ControlledRuntimeQueueAdmissionAuthorizationRequest,
        *,
        stage69_claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
        stage69_request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        stage69_result: ControlledRuntimeSchedulingEnvelopeConsumptionResult,
        stage69_verification_context: dict[str, object],
    ) -> ControlledRuntimeQueueAdmissionAuthorizationResult:
        if not isinstance(request, ControlledRuntimeQueueAdmissionAuthorizationRequest):
            raise TypeError("request must be Stage 6.10 request")
        try:
            decision = ControlledRuntimeQueueAdmissionAuthorizationDecision(
                authorization_request_id=request.authorization_request_id,
                authorization_request_fingerprint=request.request_fingerprint,
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
                unit_scope=1, authorization_status=AUTHORIZED_STATUS, reason_codes=(),
                scheduling_authorization_consumed=True,
                scheduling_envelope_prepared=True,
                scheduling_envelope_consumed=True,
                scheduling_envelope_reusable=False,
                queue_admission_authorized=True,
                queue_admission_authorization_consumed=False,
                queue_admission_record_prepared=False,
                queue_admission_record_consumed=False,
                queue_record_created=False,
                runtime_execution_scheduled=False,
                execution_started=False,
                canonical_chain=tuple(request.upstream_chain) + (request.request_fingerprint,),
            )
            verification = verify_controlled_runtime_queue_admission_authorization(
                decision, request=request, stage69_claim=stage69_claim,
                stage69_request=stage69_request, stage69_result=stage69_result,
                stage69_verification_context=stage69_verification_context,
            )
        except (TypeError, ValueError):
            return self._denied(request, ("INVARIANT_VIOLATION",))
        if not verification.valid:
            return self._denied(request, verification.reason_codes)
        return ControlledRuntimeQueueAdmissionAuthorizationResult(
            request=request, decision=decision, authorized=True,
            upstream_verified=True, status=AUTHORIZED_STATUS, reason_codes=(),
            request_count=1, decision_count=1,
        )

    @staticmethod
    def _denied(request, reasons):
        return ControlledRuntimeQueueAdmissionAuthorizationResult(
            request=request, decision=None, authorized=False,
            upstream_verified=False, status=DENIED_STATUS,
            reason_codes=tuple(reasons), request_count=1, decision_count=0,
        )
