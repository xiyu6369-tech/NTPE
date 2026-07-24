"""Atomic one-time Stage 6.8 scheduling-envelope consumer."""

from __future__ import annotations

from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelope,
    ControlledRuntimeSchedulingEnvelopeRequest,
    ControlledRuntimeSchedulingEnvelopeResult,
    verify_controlled_runtime_scheduling_envelope,
)

from .errors import (
    SchedulingEnvelopeAlreadyConsumedError,
    SchedulingEnvelopeConsumptionError,
)
from .models import (
    ControlledRuntimeSchedulingEnvelopeConsumptionClaim,
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
    ControlledRuntimeSchedulingEnvelopeConsumptionResult,
)
from .policy import SUCCESS_STATUS
from .registry import ControlledRuntimeSchedulingEnvelopeConsumptionRegistry
from .verification import (
    verify_controlled_runtime_scheduling_envelope_consumption,
)


class ControlledRuntimeSchedulingEnvelopeConsumer:
    """Consumes one authentic Stage 6.8 envelope and nothing else."""

    def consume(
        self,
        request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        *,
        scheduling_envelope: ControlledRuntimeSchedulingEnvelope,
        scheduling_envelope_request: ControlledRuntimeSchedulingEnvelopeRequest,
        scheduling_envelope_result: ControlledRuntimeSchedulingEnvelopeResult,
        stage67_scheduling_consumption_request: object,
        stage67_scheduling_consumption_claim: object,
        stage67_scheduling_consumption_result: object,
        stage66_scheduling_decision: object,
        stage65_handoff_receipt: object,
        stage64_envelope: object,
        stage63_claim: object,
        stage62_record: object,
        authorization_decision: object,
        execution_plan: object,
        database_path: str,
        allowed_root: str,
    ) -> ControlledRuntimeSchedulingEnvelopeConsumptionResult:
        if not isinstance(
            request, ControlledRuntimeSchedulingEnvelopeConsumptionRequest
        ):
            raise TypeError("request must be Stage 6.9 request")
        if not isinstance(scheduling_envelope, ControlledRuntimeSchedulingEnvelope):
            raise TypeError("scheduling_envelope must be Stage 6.8 envelope")
        if not isinstance(
            scheduling_envelope_result, ControlledRuntimeSchedulingEnvelopeResult
        ):
            raise TypeError("scheduling_envelope_result must be Stage 6.8 result")
        upstream = verify_controlled_runtime_scheduling_envelope(
            scheduling_envelope,
            request=scheduling_envelope_request,
            stage67_scheduling_consumption_request=
                stage67_scheduling_consumption_request,
            stage67_scheduling_consumption_claim=
                stage67_scheduling_consumption_claim,
            stage66_scheduling_decision=stage66_scheduling_decision,
            stage65_handoff_receipt=stage65_handoff_receipt,
            stage64_envelope=stage64_envelope,
            stage63_claim=stage63_claim,
            stage62_record=stage62_record,
            authorization_decision=authorization_decision,
            execution_plan=execution_plan,
        )
        result_authentic = all(
            (
                scheduling_envelope_result.scheduling_envelope
                == scheduling_envelope,
                scheduling_envelope_result.request
                == scheduling_envelope_request,
                scheduling_envelope_result.status
                == "scheduling_envelope_prepared_not_admitted_not_scheduled",
                not scheduling_envelope_result.scheduler_invoked,
                not scheduling_envelope_result.queue_admission_invoked,
                not scheduling_envelope_result.runtime_invoked,
                not scheduling_envelope_result.provider_invoked,
                getattr(stage67_scheduling_consumption_result, "claim", None)
                == stage67_scheduling_consumption_claim,
            )
        )
        bindings = all(
            (
                tuple(request.upstream_fingerprint_chain)
                == tuple(scheduling_envelope.upstream_fingerprint_chain),
                request.scheduling_envelope_id
                == scheduling_envelope.scheduling_envelope_id,
                request.scheduling_envelope_fingerprint
                == scheduling_envelope.scheduling_envelope_fingerprint,
                request.scheduling_envelope_request_id
                == scheduling_envelope_request.scheduling_envelope_id,
                request.scheduling_envelope_request_fingerprint
                == scheduling_envelope_request.request_fingerprint,
                request.stage67_consumption_claim_id
                == getattr(
                    stage67_scheduling_consumption_claim,
                    "scheduling_consumption_id",
                    None,
                ),
                request.stage67_claim_fingerprint
                == getattr(
                    stage67_scheduling_consumption_claim,
                    "claim_fingerprint",
                    None,
                ),
                request.stage66_scheduling_authorization_id
                == getattr(
                    stage66_scheduling_decision,
                    "scheduling_authorization_id",
                    None,
                ),
                request.stage66_decision_fingerprint
                == getattr(stage66_scheduling_decision, "decision_fingerprint", None),
                request.runtime_boundary_id
                == scheduling_envelope.runtime_boundary_id,
                request.selected_adapter_index
                == scheduling_envelope.selected_adapter_index,
            )
        )
        if not upstream.valid or not result_authentic or not bindings:
            return self._failure(
                request, "upstream_contract_mismatch", ("UPSTREAM_INVALID",)
            )
        claim = ControlledRuntimeSchedulingEnvelopeConsumptionClaim(
            consumption_request_id=request.consumption_request_id,
            consumption_request_fingerprint=request.request_fingerprint,
            scheduling_envelope_id=request.scheduling_envelope_id,
            scheduling_envelope_fingerprint=
                request.scheduling_envelope_fingerprint,
            scheduling_envelope_request_id=
                request.scheduling_envelope_request_id,
            scheduling_envelope_request_fingerprint=
                request.scheduling_envelope_request_fingerprint,
            stage67_consumption_claim_id=request.stage67_consumption_claim_id,
            stage67_claim_fingerprint=request.stage67_claim_fingerprint,
            stage66_scheduling_authorization_id=
                request.stage66_scheduling_authorization_id,
            stage66_decision_fingerprint=request.stage66_decision_fingerprint,
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
            selected_adapter_index=request.selected_adapter_index,
            unit_scope=1,
            scheduling_authorization_consumed=True,
            scheduling_envelope_prepared=True,
            scheduling_envelope_consumed=True,
            scheduling_envelope_reusable=False,
            queue_admission_authorized=False,
            runtime_execution_scheduled=False,
            queue_record_created=False,
            execution_started=False,
            persistent_registry_written=True,
            claim_state=SUCCESS_STATUS,
            canonical_chain=tuple(request.upstream_fingerprint_chain)
            + (request.request_fingerprint,),
        )
        registry = ControlledRuntimeSchedulingEnvelopeConsumptionRegistry(
            database_path, allowed_root=allowed_root
        )
        try:
            stored = registry.claim(request, claim)
        except SchedulingEnvelopeAlreadyConsumedError:
            return ControlledRuntimeSchedulingEnvelopeConsumptionResult(
                request=request,
                claim=None,
                verification_succeeded=False,
                upstream_verification_succeeded=True,
                durable_claim_created=False,
                exactly_one_envelope_consumed=False,
                replay_detected=True,
                persistence_committed=False,
                durable_readback_verified=False,
                status="already_consumed",
                reason_codes=("ALREADY_CONSUMED",),
            )
        except SchedulingEnvelopeConsumptionError as exc:
            return self._failure(
                request, "registry_error", (type(exc).__name__,)
            )
        verification = verify_controlled_runtime_scheduling_envelope_consumption(
            stored,
            request=request,
            scheduling_envelope=scheduling_envelope,
            scheduling_envelope_request=scheduling_envelope_request,
            stage67_scheduling_consumption_request=
                stage67_scheduling_consumption_request,
            stage67_scheduling_consumption_claim=
                stage67_scheduling_consumption_claim,
            stage66_scheduling_decision=stage66_scheduling_decision,
            stage65_handoff_receipt=stage65_handoff_receipt,
            stage64_envelope=stage64_envelope,
            stage63_claim=stage63_claim,
            stage62_record=stage62_record,
            authorization_decision=authorization_decision,
            execution_plan=execution_plan,
            persisted_payload_json=stored.to_json(),
            persistence_committed=True,
        )
        if not verification.valid:
            return self._failure(
                request, "verification_failed", verification.reason_codes
            )
        return ControlledRuntimeSchedulingEnvelopeConsumptionResult(
            request=request,
            claim=stored,
            verification_succeeded=True,
            upstream_verification_succeeded=True,
            durable_claim_created=True,
            exactly_one_envelope_consumed=True,
            replay_detected=False,
            persistence_committed=True,
            durable_readback_verified=True,
            status=SUCCESS_STATUS,
            reason_codes=(),
        )

    @staticmethod
    def _failure(
        request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
        status: str,
        reasons: tuple[str, ...],
    ) -> ControlledRuntimeSchedulingEnvelopeConsumptionResult:
        return ControlledRuntimeSchedulingEnvelopeConsumptionResult(
            request=request,
            claim=None,
            verification_succeeded=False,
            upstream_verification_succeeded=False,
            durable_claim_created=False,
            exactly_one_envelope_consumed=False,
            replay_detected=False,
            persistence_committed=False,
            durable_readback_verified=False,
            status=status,
            reason_codes=reasons,
        )
