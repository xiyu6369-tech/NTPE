"""Pure, fail-closed Stage 6.5 Runtime handoff acceptance boundary."""

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

from .models import (
    ControlledRuntimeHandoffFinding,
    ControlledRuntimeHandoffReceipt,
    ControlledRuntimeHandoffRequest,
    ControlledRuntimeHandoffResult,
    canonical_sha256,
)
from .policy import (
    BOUNDARY_KIND,
    DEFAULT_POLICY,
    SUCCESS_ACTION,
    SUCCESS_STATUS,
    ControlledRuntimeHandoffPolicy,
    exact_handoff_scope,
)


def _finding(code: str, field: str = "", expected: str = "", observed: str = ""):
    return ControlledRuntimeHandoffFinding(
        code=code, severity="blocking", message=code.replace("_", " ").lower(),
        field=field, expected=expected, observed=observed,
    )


class ControlledRuntimeHandoffBoundary:
    """A stateless in-memory contract boundary; it has no execution capabilities."""

    __slots__ = ("_policy", "_runtime_boundary_id")

    def __init__(
        self, *, runtime_boundary_id: str = "offline-runtime-boundary-001",
        policy: ControlledRuntimeHandoffPolicy = DEFAULT_POLICY,
    ):
        if (
            not isinstance(runtime_boundary_id, str)
            or not runtime_boundary_id
            or len(runtime_boundary_id) > policy.max_boundary_id_length
        ):
            raise ValueError("runtime_boundary_id must be a known bounded identity")
        object.__setattr__(self, "_policy", policy)
        object.__setattr__(self, "_runtime_boundary_id", runtime_boundary_id)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("ControlledRuntimeHandoffBoundary state is immutable")
        object.__setattr__(self, name, value)

    def accept(
        self,
        *,
        request: ControlledRuntimeHandoffRequest,
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
    ) -> ControlledRuntimeHandoffResult:
        findings: list[ControlledRuntimeHandoffFinding] = []
        flags = {
            "freeze_gate_verified": True, "execution_plan_verified": True,
            "authorization_verified": True, "stage62_verified": True,
            "stage63_claim_verified": True,
            "stage64_envelope_request_verified": True,
            "stage64_envelope_verified": True, "stage64_result_verified": True,
            "authorization_binding_verified": True,
            "claim_binding_verified": True, "envelope_binding_verified": True,
            "adapter_index_verified": True, "execution_unit_verified": True,
            "runtime_boundary_verified": True, "handoff_scope_verified": True,
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
            getattr(plan, "schema_name", None) == "ntpe.controlled_runtime_execution_plan",
            getattr(plan, "execution_plan_fingerprint", None)
            == request.execution_plan_fingerprint,
            getattr(plan, "status", None) in ("planned_not_executed", "planned_with_warnings"),
            not getattr(plan, "execution_started", True),
            not getattr(plan, "execution_completed", True),
            getattr(plan, "provider_requests_executed", -1) == 0,
            getattr(plan, "translation_executions_completed", -1) == 0,
            tuple(getattr(plan, "selected_adapter_unit_indices", ()))
            == (request.selected_adapter_index,),
            getattr(getattr(plan, "policy", None), "maximum_total_provider_requests", None) == 1,
            all(getattr(step, "planned_provider_request_limit", None) == 1 for step in getattr(plan, "steps", ())),
            all(getattr(step, "planned_retry_limit", None) == 0 for step in getattr(plan, "steps", ())),
            all(getattr(step, "planned_fallback_limit", None) == 0 for step in getattr(plan, "steps", ())),
        ))
        if not plan_ok:
            fail("execution_plan_verified", "EXECUTION_PLAN_INVALID")

        auth_ok = all((
            getattr(authorization_request, "request_fingerprint", None)
            == getattr(authorization_decision, "authorization_request_fingerprint", None),
            getattr(authorization_decision, "decision_fingerprint", None)
            == request.authorization_decision_fingerprint,
            getattr(authorization_decision, "authorization_id", None)
            == request.authorization_id,
            getattr(authorization_decision, "authorized", False),
            not getattr(authorization_decision, "authorization_reusable", True),
            getattr(authorization_decision, "status", None) == "authorized_not_executed",
            getattr(authorization_result, "status", None) == "authorized_not_executed",
            getattr(authorization_decision, "authorized_provider_request_limit", None) == 1,
            getattr(authorization_decision, "authorized_retry_limit", None) == 0,
            getattr(authorization_decision, "authorized_fallback_limit", None) == 0,
        ))
        if not auth_ok:
            fail("authorization_verified", "AUTHORIZATION_INVALID")

        stage62_check = verify_consumption_record(
            stage62_record,
            request_fingerprint=getattr(stage62_request, "request_fingerprint", ""),
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=getattr(
                authorization_request, "request_fingerprint", ""
            ),
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
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
            stage63_claim,
            request=stage63_claim_request,
            stage62_request=stage62_request,
            stage62_record=stage62_record,
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
        if getattr(stage64_check, "status", None) != "runtime_handoff_prepared_not_executed":
            fail("stage64_envelope_verified", "STAGE64_ENVELOPE_INVALID")
        if not (
            getattr(stage64_envelope_request, "request_fingerprint", None)
            == request.stage64_envelope_request_fingerprint
            == getattr(stage64_envelope, "envelope_request_fingerprint", None)
        ):
            fail("stage64_envelope_request_verified", "STAGE64_REQUEST_INVALID")
        if not (
            getattr(stage64_result, "status", None)
            == "runtime_handoff_prepared_not_executed"
            and getattr(stage64_result, "recommended_action", None)
            == "retain_for_controlled_runtime_handoff"
            and getattr(stage64_result, "request", None) == stage64_envelope_request
            and getattr(stage64_result, "envelope", None) == stage64_envelope
            and not any(getattr(stage64_result, name, True) for name in (
                "runtime_invoked", "provider_invoked", "network_invoked",
                "translation_invoked",
            ))
        ):
            fail("stage64_result_verified", "STAGE64_RESULT_INVALID")

        expected_scope = exact_handoff_scope(
            envelope_id=request.envelope_id,
            authorization_id=request.authorization_id,
            claim_id=request.claim_id,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            runtime_boundary_id=request.runtime_boundary_id,
        )
        bindings = (
            ("envelope_binding_verified", "ENVELOPE_BINDING_MISMATCH", all((
                request.envelope_id == getattr(stage64_envelope, "envelope_id", None),
                request.stage64_envelope_fingerprint
                == getattr(stage64_envelope, "envelope_fingerprint", None),
            ))),
            ("claim_binding_verified", "CLAIM_BINDING_MISMATCH", all((
                request.claim_id == getattr(stage63_claim, "claim_id", None),
                request.stage63_claim_fingerprint
                == getattr(stage63_claim, "claim_fingerprint", None),
            ))),
            ("authorization_binding_verified", "AUTHORIZATION_BINDING_MISMATCH",
             request.authorization_id == getattr(authorization_decision, "authorization_id", None)),
            ("adapter_index_verified", "ADAPTER_INDEX_MISMATCH", all(
                request.selected_adapter_index == value for value in (
                    getattr(stage63_claim, "selected_adapter_index", None),
                    getattr(stage64_envelope, "selected_adapter_index", None),
                )
            )),
            ("execution_unit_verified", "EXECUTION_UNIT_MISMATCH", all((
                type(request.requested_unit_count) is int,
                request.requested_unit_count == 1,
                getattr(stage64_envelope, "execution_unit_count", None) == 1,
            ))),
            ("runtime_boundary_verified", "RUNTIME_BOUNDARY_MISMATCH",
             request.runtime_boundary_kind == BOUNDARY_KIND
             and request.runtime_boundary_id == self._runtime_boundary_id),
            ("handoff_scope_verified", "HANDOFF_SCOPE_MISMATCH",
             request.handoff_scope == expected_scope),
        )
        for flag, code, passed in bindings:
            if not passed:
                fail(flag, code)
        if request.request_fingerprint != canonical_sha256(request._fingerprint_payload()):
            findings.append(_finding("REQUEST_FINGERPRINT_MISMATCH"))

        if findings:
            status = (
                "handoff_scope_mismatch"
                if not flags["handoff_scope_verified"]
                else "runtime_boundary_mismatch"
                if not flags["runtime_boundary_verified"]
                else "envelope_not_eligible"
                if not flags["stage64_envelope_verified"]
                else "upstream_contract_mismatch"
            )
            return ControlledRuntimeHandoffResult(
                request=request, receipt=None, policy_findings=tuple(findings),
                status=status, recommended_action="do_not_schedule",
                runtime_boundary_invoked=True, **flags,
            )

        receipt = ControlledRuntimeHandoffReceipt(
            handoff_id=request.handoff_id, envelope_id=request.envelope_id,
            claim_id=request.claim_id, consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            stage63_claim_fingerprint=request.stage63_claim_fingerprint,
            stage64_envelope_request_fingerprint=request.stage64_envelope_request_fingerprint,
            stage64_envelope_fingerprint=request.stage64_envelope_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            accepted_unit_count=1, runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
            authorization_consumed=True, authorization_reusable=False,
            durable_reuse_prevention_established=True,
            persistent_registry_written=True, runtime_handoff_prepared=True,
            runtime_handoff_completed=True, runtime_boundary_accepted=True,
            runtime_execution_scheduled=False, execution_started=False,
            execution_completed=False, runtime_execution_enabled=False,
            provider_execution_enabled=False, network_execution_enabled=False,
            translation_execution_enabled=False, output_write_enabled=False,
            resume_write_enabled=False, cache_write_enabled=False,
            retry_enabled=False, fallback_enabled=False,
            production_hook_enabled=False, receipt_state=SUCCESS_STATUS,
            upstream_fingerprint_chain=tuple(stage64_envelope.upstream_fingerprint_chain)
            + (request.request_fingerprint,),
            handoff_request_fingerprint=request.request_fingerprint,
        )
        return ControlledRuntimeHandoffResult(
            request=request, receipt=receipt, policy_findings=(),
            status=SUCCESS_STATUS, recommended_action=SUCCESS_ACTION,
            runtime_boundary_invoked=True, **flags,
        )
