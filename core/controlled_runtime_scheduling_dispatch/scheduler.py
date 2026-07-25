"""Controlled Stage 7.2 scheduling without executor invocation."""

from __future__ import annotations

from .errors import (
    ControlledRuntimeAlreadyScheduledError,
    ControlledRuntimeSchedulingConflictError,
    ControlledRuntimeSchedulingDispatchError,
    ControlledRuntimeSchedulingDispatchPolicyError,
)
from .models import (
    ControlledRuntimeDispatchPackage,
    ControlledRuntimeExecutionSchedule,
    ControlledRuntimeSchedulingRequest,
    ControlledRuntimeSchedulingResult,
)
from .policy import FAILURE_STATUS, SCHEDULE_STATE, SUCCESS_STATUS
from .registry import ControlledRuntimeSchedulingRegistry
from .serialization import canonical_sha256
from .verification import verify_controlled_runtime_scheduling_dispatch

_BINDINGS = (
    "queue_record_id",
    "queue_record_fingerprint",
    "admission_request_id",
    "admission_request_fingerprint",
    "stage613_claim_id",
    "stage613_claim_fingerprint",
    "stage612_record_id",
    "stage612_record_fingerprint",
    "stage611_claim_id",
    "stage611_claim_fingerprint",
    "stage610_authorization_id",
    "stage610_decision_fingerprint",
    "stage69_consumption_claim_id",
    "stage69_claim_fingerprint",
    "stage68_scheduling_envelope_id",
    "stage68_envelope_fingerprint",
    "stage67_consumption_claim_id",
    "stage67_claim_fingerprint",
    "stage66_scheduling_authorization_id",
    "stage66_decision_fingerprint",
    "runtime_boundary_id",
    "runtime_boundary_kind",
    "selected_adapter_index",
    "capability_state_fingerprint",
    "admission_class",
    "priority_class",
    "ordering_key",
    "unit_scope",
    "execution_plan_reference_fingerprint",
    "work_package_reference_fingerprint",
)


class ControlledRuntimeScheduler:
    """Atomically consume one Stage 7.1 authority and prepare dispatch."""

    def schedule(
        self,
        request: ControlledRuntimeSchedulingRequest,
        *,
        queue_record,
        stage71_request,
        stage71_result,
        stage613_claim,
        stage613_request,
        stage613_result,
        stage613_verification_context,
        database_path,
        allowed_root,
    ) -> ControlledRuntimeSchedulingResult:
        if not isinstance(request, ControlledRuntimeSchedulingRequest):
            raise TypeError("request must be a Stage 7.2 scheduling request")
        bindings = {name: getattr(request, name) for name in _BINDINGS}
        dispatch_key = canonical_sha256(
            {
                "queue_record_id": request.queue_record_id,
                "queue_record_fingerprint": request.queue_record_fingerprint,
                "ordering_key": request.ordering_key,
                "unit_scope": request.unit_scope,
            }
        )
        schedule = ControlledRuntimeExecutionSchedule(
            scheduling_request_id=request.scheduling_request_id,
            scheduling_request_fingerprint=request.request_fingerprint,
            dispatch_key=dispatch_key,
            schedule_state=SCHEDULE_STATE,
            queue_record_created=True,
            queue_record_consumed=True,
            queue_record_reusable=False,
            runtime_execution_scheduled=True,
            dispatch_package_created=True,
            execution_started=False,
            runtime_executor_invoked=False,
            worker_started=False,
            provider_execution_started=False,
            translation_execution_started=False,
            output_written=False,
            canonical_chain=tuple(request.upstream_chain)
            + (request.request_fingerprint,),
            **bindings,
        )
        dispatch = ControlledRuntimeDispatchPackage(
            schedule_id=schedule.schedule_id,
            schedule_fingerprint=schedule.schedule_fingerprint,
            scheduling_request_id=request.scheduling_request_id,
            scheduling_request_fingerprint=request.request_fingerprint,
            dispatch_key=dispatch_key,
            dispatch_package_created=True,
            execution_started=False,
            runtime_executor_invoked=False,
            worker_started=False,
            provider_execution_started=False,
            translation_execution_started=False,
            output_written=False,
            canonical_chain=tuple(schedule.canonical_chain),
            **bindings,
        )
        registry = ControlledRuntimeSchedulingRegistry(
            database_path, allowed_root=allowed_root
        )
        authority = dict(
            queue_record=queue_record,
            stage71_request=stage71_request,
            stage71_result=stage71_result,
            stage613_claim=stage613_claim,
            stage613_request=stage613_request,
            stage613_result=stage613_result,
            stage613_verification_context=stage613_verification_context,
        )
        try:
            stored_schedule, stored_dispatch = registry.schedule(
                request, schedule, dispatch, **authority
            )
        except ControlledRuntimeAlreadyScheduledError:
            return self._denied(
                request,
                ("ALREADY_SCHEDULED",),
                replay=True,
                upstream_verified=True,
            )
        except ControlledRuntimeSchedulingConflictError:
            return self._denied(
                request,
                ("CONFLICT",),
                conflict=True,
                upstream_verified=True,
            )
        except ControlledRuntimeSchedulingDispatchPolicyError as error:
            return self._denied(request, error.reason_codes)
        except ControlledRuntimeSchedulingDispatchError:
            return self._denied(request, ("REGISTRY_ERROR",))
        candidate = ControlledRuntimeSchedulingResult(
            request=request,
            schedule=stored_schedule,
            dispatch_package=stored_dispatch,
            verification_succeeded=True,
            upstream_verified=True,
            queue_record_consumed=True,
            runtime_execution_scheduled=True,
            dispatch_package_created=True,
            replay_detected=False,
            conflict_detected=False,
            persistence_committed=True,
            schedule_readback_verified=True,
            dispatch_readback_verified=True,
            status=SUCCESS_STATUS,
            reason_codes=(),
            queue_record_consumed_count=1,
            runtime_schedule_count=1,
            dispatch_package_count=1,
        )
        verification = verify_controlled_runtime_scheduling_dispatch(
            stored_schedule,
            stored_dispatch,
            request=request,
            result=candidate,
            persisted_schedule_payload_json=stored_schedule.to_json(),
            persisted_dispatch_payload_json=stored_dispatch.to_json(),
            persistence_committed=True,
            schedule_readback_verified=True,
            dispatch_readback_verified=True,
            **authority,
        )
        if type(verification.valid) is not bool or verification.valid is not True:
            return self._denied(
                request,
                verification.reason_codes,
                upstream_verified=True,
                persistence_committed=True,
            )
        return candidate

    @staticmethod
    def _denied(
        request,
        reasons,
        *,
        replay=False,
        conflict=False,
        upstream_verified=False,
        persistence_committed=False,
    ):
        return ControlledRuntimeSchedulingResult(
            request=request,
            schedule=None,
            dispatch_package=None,
            verification_succeeded=False,
            upstream_verified=upstream_verified,
            queue_record_consumed=False,
            runtime_execution_scheduled=False,
            dispatch_package_created=False,
            replay_detected=replay,
            conflict_detected=conflict,
            persistence_committed=persistence_committed,
            schedule_readback_verified=False,
            dispatch_readback_verified=False,
            status=FAILURE_STATUS,
            reason_codes=tuple(reasons),
            queue_record_consumed_count=0,
            runtime_schedule_count=0,
            dispatch_package_count=0,
        )
