"""Pure fail-closed Stage 6.6 scheduling authorizer."""

from __future__ import annotations

from core.controlled_runtime_atomic_authorization_consumption.verification import (
    verify_atomic_consumption_claim,
)
from core.controlled_runtime_authorization_consumption.verification import (
    verify_consumption_record,
)
from core.controlled_runtime_execution_envelope.verification import (
    verify_execution_envelope,
)
from core.controlled_runtime_handoff_boundary import (
    verify_runtime_handoff_receipt,
)

from .models import (
    ControlledRuntimeSchedulingAuthorizationDecision,
    ControlledRuntimeSchedulingAuthorizationFinding,
    ControlledRuntimeSchedulingAuthorizationRequest,
    ControlledRuntimeSchedulingAuthorizationResult,
    canonical_sha256,
)
from .policy import (
    BOUNDARY_KIND,
    DEFAULT_POLICY,
    SUCCESS_ACTION,
    SUCCESS_STATUS,
    ControlledRuntimeSchedulingAuthorizationPolicy,
    exact_scheduling_scope,
)


def _finding(code: str, field: str = ""):
    return ControlledRuntimeSchedulingAuthorizationFinding(
        code=code, severity="blocking",
        message=code.replace("_", " ").lower(), field=field,
    )


class ControlledRuntimeSchedulingAuthorizer:
    """Stateless in-memory authorization only; it cannot schedule."""

    __slots__ = ("_policy",)

    def __init__(
        self,
        *,
        policy: ControlledRuntimeSchedulingAuthorizationPolicy = DEFAULT_POLICY,
    ):
        if policy != DEFAULT_POLICY:
            raise ValueError("Stage 6.6 policy may not be changed")
        object.__setattr__(self, "_policy", policy)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("authorizer state is immutable")
        object.__setattr__(self, name, value)

    def authorize(
        self,
        *,
        request: ControlledRuntimeSchedulingAuthorizationRequest,
        freeze_validation: object,
        execution_plan: object,
        authorization_request: object,
        authorization_decision: object,
        authorization_result: object,
        stage62_request: object,
        stage62_record: object,
        stage62_result: object,
        stage63_claim_request: object,
        stage63_claim: object,
        stage63_result: object,
        stage64_envelope_request: object,
        stage64_envelope: object,
        stage64_result: object,
        stage65_handoff_request: object,
        stage65_handoff_receipt: object,
        stage65_result: object,
    ) -> ControlledRuntimeSchedulingAuthorizationResult:
        if not isinstance(
            request, ControlledRuntimeSchedulingAuthorizationRequest
        ):
            raise TypeError("request must be Stage 6.6 authorization request")
        findings: list[ControlledRuntimeSchedulingAuthorizationFinding] = []
        flags = {
            "freeze_gate_verified": True,
            "execution_plan_verified": True,
            "execution_authorization_verified": True,
            "stage62_verified": True,
            "stage63_claim_verified": True,
            "stage64_envelope_verified": True,
            "stage65_handoff_request_verified": True,
            "stage65_handoff_receipt_verified": True,
            "stage65_result_verified": True,
            "authorization_binding_verified": True,
            "claim_binding_verified": True,
            "envelope_binding_verified": True,
            "handoff_binding_verified": True,
            "adapter_index_verified": True,
            "schedule_unit_verified": True,
            "runtime_boundary_verified": True,
            "scheduling_scope_verified": True,
        }

        def fail(flag: str, code: str, field: str = "") -> None:
            flags[flag] = False
            findings.append(_finding(code, field))

        if not all((
            getattr(freeze_validation, "valid", False),
            getattr(freeze_validation, "activation_gate", None)
            == "controlled_runtime_preparation_frozen",
            getattr(freeze_validation, "frozen_file_count", None) == 16,
            getattr(freeze_validation, "public_api_count", None) == 41,
            getattr(freeze_validation, "invariant_count", None) == 49,
        )):
            fail("freeze_gate_verified", "FREEZE_GATE_INVALID")

        plan = execution_plan
        plan_ok = all((
            getattr(plan, "schema_name", None)
            == "ntpe.controlled_runtime_execution_plan",
            getattr(plan, "status", None)
            in ("planned_not_executed", "planned_with_warnings"),
            not getattr(plan, "execution_started", True),
            not getattr(plan, "execution_completed", True),
            getattr(plan, "provider_requests_executed", -1) == 0,
            getattr(plan, "translation_executions_completed", -1) == 0,
            tuple(getattr(plan, "selected_adapter_unit_indices", ()))
            == (request.selected_adapter_index,),
            getattr(getattr(plan, "policy", None),
                    "maximum_total_provider_requests", None) == 1,
            all(
                getattr(step, "planned_provider_request_limit", None) == 1
                and getattr(step, "planned_retry_limit", None) == 0
                and getattr(step, "planned_fallback_limit", None) == 0
                and getattr(step, "runtime_attempt_count", None) == 0
                and getattr(step, "provider_request_count", None) == 0
                and not getattr(step, "translation_result_attached", True)
                for step in getattr(plan, "steps", ())
            ),
        ))
        if not plan_ok:
            fail("execution_plan_verified", "EXECUTION_PLAN_INVALID")

        auth_ok = all((
            getattr(authorization_request, "request_fingerprint", None)
            == getattr(authorization_decision,
                       "authorization_request_fingerprint", None),
            getattr(authorization_decision, "decision_fingerprint", None)
            == request.execution_authorization_decision_fingerprint,
            getattr(authorization_decision, "authorization_id", None)
            == request.authorization_id,
            getattr(authorization_decision, "authorized", False),
            not getattr(authorization_decision, "authorization_reusable", True),
            getattr(authorization_decision, "status", None)
            == "authorized_not_executed",
            getattr(authorization_result, "status", None)
            == "authorized_not_executed",
        ))
        if not auth_ok:
            fail("execution_authorization_verified", "AUTHORIZATION_INVALID")

        stage62_check = verify_consumption_record(
            stage62_record,
            request_fingerprint=getattr(stage62_request, "request_fingerprint", ""),
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=getattr(
                authorization_request, "request_fingerprint", ""
            ),
            authorization_decision_fingerprint=
                request.execution_authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            adapter_index=request.selected_adapter_index,
            unit_count=1,
        )
        if not (
            stage62_check.valid
            and getattr(stage62_result, "status", None)
            == "consumption_prepared_not_executed"
        ):
            fail("stage62_verified", "STAGE62_INVALID")

        stage63_check = verify_atomic_consumption_claim(
            stage63_claim, request=stage63_claim_request,
            stage62_request=stage62_request, stage62_record=stage62_record,
            authorization_request=authorization_request,
            authorization_decision=authorization_decision,
            execution_plan=execution_plan,
        )
        if not (
            stage63_check.valid
            and getattr(stage63_result, "status", None)
            == "durably_consumed_not_executed"
        ):
            fail("stage63_claim_verified", "STAGE63_INVALID")

        stage64_check = verify_execution_envelope(stage64_envelope)
        if not (
            getattr(stage64_check, "status", None)
            == "runtime_handoff_prepared_not_executed"
            and getattr(stage64_result, "status", None)
            == "runtime_handoff_prepared_not_executed"
            and getattr(stage64_result, "envelope", None) == stage64_envelope
        ):
            fail("stage64_envelope_verified", "STAGE64_INVALID")

        stage65_check = verify_runtime_handoff_receipt(
            stage65_handoff_receipt,
            request=stage65_handoff_request,
            execution_plan=execution_plan,
            authorization_request=authorization_request,
            authorization_decision=authorization_decision,
            stage62_request=stage62_request, stage62_record=stage62_record,
            stage63_claim_request=stage63_claim_request,
            stage63_claim=stage63_claim,
            stage64_envelope_request=stage64_envelope_request,
            stage64_envelope=stage64_envelope,
        )
        if not stage65_check.valid:
            fail("stage65_handoff_receipt_verified", "STAGE65_RECEIPT_INVALID")
        if not (
            getattr(stage65_handoff_request, "request_fingerprint", None)
            == request.stage65_handoff_request_fingerprint
        ):
            fail("stage65_handoff_request_verified", "STAGE65_REQUEST_INVALID")
        if not (
            getattr(stage65_result, "status", None)
            == "handoff_accepted_not_scheduled_not_executed"
            and getattr(stage65_result, "recommended_action", None)
            == "retain_for_controlled_scheduling_authorization"
            and getattr(stage65_result, "request", None)
            == stage65_handoff_request
            and getattr(stage65_result, "receipt", None)
            == stage65_handoff_receipt
            and getattr(stage65_result, "runtime_boundary_invoked", False)
            and not any(getattr(stage65_result, name, True) for name in (
                "runtime_scheduled", "runtime_invoked", "provider_invoked",
                "network_invoked", "translation_invoked", "output_written",
                "resume_written", "cache_written", "retry_used",
                "fallback_used", "production_hook_invoked",
            ))
        ):
            fail("stage65_result_verified", "STAGE65_RESULT_INVALID")

        receipt = stage65_handoff_receipt
        bindings = (
            ("authorization_binding_verified", "AUTHORIZATION_BINDING_MISMATCH",
             all((
                 request.authorization_id
                 == getattr(receipt, "authorization_id", None),
                 request.execution_authorization_decision_fingerprint
                 == getattr(receipt, "authorization_decision_fingerprint", None),
             ))),
            ("claim_binding_verified", "CLAIM_BINDING_MISMATCH", all((
                request.claim_id == getattr(receipt, "claim_id", None),
                request.stage63_claim_fingerprint
                == getattr(receipt, "stage63_claim_fingerprint", None),
            ))),
            ("envelope_binding_verified", "ENVELOPE_BINDING_MISMATCH", all((
                request.envelope_id == getattr(receipt, "envelope_id", None),
                request.stage64_envelope_fingerprint
                == getattr(receipt, "stage64_envelope_fingerprint", None),
            ))),
            ("handoff_binding_verified", "HANDOFF_BINDING_MISMATCH", all((
                request.handoff_id == getattr(receipt, "handoff_id", None),
                request.stage65_handoff_receipt_fingerprint
                == getattr(receipt, "receipt_fingerprint", None),
            ))),
            ("adapter_index_verified", "ADAPTER_INDEX_MISMATCH",
             all(request.selected_adapter_index == value for value in (
                 getattr(receipt, "selected_adapter_index", None),
                 getattr(stage64_envelope, "selected_adapter_index", None),
                 getattr(stage63_claim, "selected_adapter_index", None),
             ))),
            ("schedule_unit_verified", "SCHEDULE_UNIT_MISMATCH", all((
                type(request.requested_schedule_unit_count) is int,
                request.requested_schedule_unit_count == 1,
                getattr(receipt, "accepted_unit_count", None) == 1,
            ))),
            ("runtime_boundary_verified", "RUNTIME_BOUNDARY_MISMATCH", all((
                request.runtime_boundary_id
                == getattr(receipt, "runtime_boundary_id", None),
                request.runtime_boundary_kind
                == getattr(receipt, "runtime_boundary_kind", None)
                == BOUNDARY_KIND,
            ))),
        )
        for flag, code, passed in bindings:
            if not passed:
                fail(flag, code)

        expected_scope = exact_scheduling_scope(
            handoff_id=request.handoff_id, envelope_id=request.envelope_id,
            claim_id=request.claim_id, consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            execution_authorization_decision_fingerprint=
                request.execution_authorization_decision_fingerprint,
            stage63_claim_fingerprint=request.stage63_claim_fingerprint,
            stage64_envelope_fingerprint=request.stage64_envelope_fingerprint,
            stage65_handoff_receipt_fingerprint=
                request.stage65_handoff_receipt_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            runtime_boundary_id=request.runtime_boundary_id,
        )
        if request.scheduling_scope != expected_scope:
            fail("scheduling_scope_verified", "SCHEDULING_SCOPE_MISMATCH")
        if request.request_fingerprint != canonical_sha256(
            request._fingerprint_payload()
        ):
            findings.append(_finding("REQUEST_FINGERPRINT_MISMATCH"))

        if findings:
            status = (
                "scheduling_scope_mismatch"
                if not flags["scheduling_scope_verified"]
                else "runtime_boundary_mismatch"
                if not flags["runtime_boundary_verified"]
                else "handoff_not_eligible"
                if not flags["stage65_handoff_receipt_verified"]
                else "upstream_contract_mismatch"
            )
            return ControlledRuntimeSchedulingAuthorizationResult(
                request=request, decision=None, policy_findings=tuple(findings),
                status=status, recommended_action="do_not_schedule",
                authorizer_invoked=True, **flags,
            )

        decision = ControlledRuntimeSchedulingAuthorizationDecision(
            scheduling_authorization_id=request.scheduling_authorization_id,
            handoff_id=request.handoff_id, envelope_id=request.envelope_id,
            claim_id=request.claim_id, consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            execution_authorization_decision_fingerprint=
                request.execution_authorization_decision_fingerprint,
            stage63_claim_fingerprint=request.stage63_claim_fingerprint,
            stage64_envelope_fingerprint=request.stage64_envelope_fingerprint,
            stage65_handoff_request_fingerprint=
                request.stage65_handoff_request_fingerprint,
            stage65_handoff_receipt_fingerprint=
                request.stage65_handoff_receipt_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            authorized_schedule_unit_count=1,
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
            authorization_consumed=True, authorization_reusable=False,
            durable_reuse_prevention_established=True,
            persistent_registry_written=True,
            runtime_handoff_prepared=True, runtime_handoff_completed=True,
            runtime_boundary_accepted=True,
            scheduling_authorization_requested=True,
            scheduling_authorized=True,
            scheduling_authorization_consumed=False,
            scheduling_authorization_reusable=False, schedule_once=True,
            runtime_execution_scheduled=False, queue_record_created=False,
            job_record_created=False, worker_started=False,
            execution_started=False, execution_completed=False,
            runtime_execution_enabled=False, provider_execution_enabled=False,
            network_execution_enabled=False,
            translation_execution_enabled=False, output_write_enabled=False,
            resume_write_enabled=False, cache_write_enabled=False,
            retry_enabled=False, fallback_enabled=False,
            production_hook_enabled=False, decision_state=SUCCESS_STATUS,
            upstream_fingerprint_chain=tuple(
                getattr(receipt, "upstream_fingerprint_chain", ())
            ) + (request.request_fingerprint,),
            scheduling_authorization_request_fingerprint=
                request.request_fingerprint,
        )
        return ControlledRuntimeSchedulingAuthorizationResult(
            request=request, decision=decision, policy_findings=(),
            status=SUCCESS_STATUS, recommended_action=SUCCESS_ACTION,
            authorizer_invoked=True, **flags,
        )
