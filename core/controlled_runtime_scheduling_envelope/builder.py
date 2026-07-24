"""Stateless fail-closed Stage 6.8 scheduling-envelope builder."""

from __future__ import annotations

from typing import Any

from core.controlled_runtime_atomic_authorization_consumption.verification import (
    verify_atomic_consumption_claim,
)
from core.controlled_runtime_atomic_scheduling_consumption.verification import (
    verify_atomic_scheduling_consumption_claim,
)
from core.controlled_runtime_authorization_consumption.verification import (
    verify_consumption_record,
)
from core.controlled_runtime_execution_envelope.verification import (
    verify_execution_envelope,
)
from core.controlled_runtime_handoff_boundary.verification import (
    verify_runtime_handoff_receipt,
)
from core.controlled_runtime_scheduling_authorization.verification import (
    verify_scheduling_authorization_decision,
)

from .models import (
    ControlledRuntimeSchedulingEnvelope,
    ControlledRuntimeSchedulingEnvelopeFinding,
    ControlledRuntimeSchedulingEnvelopeRequest,
    ControlledRuntimeSchedulingEnvelopeResult,
    canonical_sha256,
)
from .policy import (
    DEFAULT_POLICY,
    SUCCESS_ACTION,
    SUCCESS_STATUS,
    exact_scheduling_scope,
)
from .verification import verify_controlled_runtime_scheduling_envelope

_FLAG_NAMES = (
    "freeze_gate_verified",
    "execution_plan_verified",
    "execution_authorization_verified",
    "stage62_verified",
    "stage63_claim_verified",
    "stage64_envelope_verified",
    "stage65_handoff_receipt_verified",
    "stage66_scheduling_request_verified",
    "stage66_scheduling_decision_verified",
    "stage66_result_verified",
    "stage67_scheduling_consumption_request_verified",
    "stage67_scheduling_consumption_claim_verified",
    "stage67_result_verified",
    "authorization_binding_verified",
    "claim_binding_verified",
    "execution_envelope_binding_verified",
    "handoff_binding_verified",
    "scheduling_authorization_binding_verified",
    "scheduling_consumption_binding_verified",
    "adapter_index_verified",
    "schedule_unit_verified",
    "runtime_boundary_verified",
    "scheduling_scope_verified",
)


def _finding(code: str, field: str = "") -> ControlledRuntimeSchedulingEnvelopeFinding:
    return ControlledRuntimeSchedulingEnvelopeFinding(
        code=code,
        severity="blocking",
        message=code.replace("_", " ").lower(),
        field=field,
    )


class ControlledRuntimeSchedulingEnvelopeBuilder:
    """Builds one immutable envelope without admission or scheduling."""

    __slots__ = ("_policy",)

    def __init__(self, *, policy=DEFAULT_POLICY) -> None:
        if policy != DEFAULT_POLICY:
            raise ValueError("Stage 6.8 policy may not be changed")
        object.__setattr__(self, "_policy", policy)

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, name):
            raise AttributeError("builder state is immutable")
        object.__setattr__(self, name, value)

    def build(
        self,
        request: ControlledRuntimeSchedulingEnvelopeRequest,
        *,
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
        stage66_scheduling_request: object,
        stage66_scheduling_decision: object,
        stage66_scheduling_result: object,
        stage67_scheduling_consumption_request: object,
        stage67_scheduling_consumption_claim: object,
        stage67_scheduling_consumption_result: object,
    ) -> ControlledRuntimeSchedulingEnvelopeResult:
        if not isinstance(request, ControlledRuntimeSchedulingEnvelopeRequest):
            raise TypeError("request must be a Stage 6.8 request")
        flags = {name: True for name in _FLAG_NAMES}
        findings: list[ControlledRuntimeSchedulingEnvelopeFinding] = []

        def fail(flag: str, code: str) -> None:
            flags[flag] = False
            findings.append(_finding(code))

        if request.request_fingerprint != canonical_sha256(
            request._fingerprint_payload()
        ):
            fail("scheduling_scope_verified", "REQUEST_FINGERPRINT_MISMATCH")
        expected_scope = exact_scheduling_scope(
            scheduling_consumption_id=request.scheduling_consumption_id,
            scheduling_authorization_id=request.scheduling_authorization_id,
            handoff_id=request.handoff_id,
            envelope_id=request.envelope_id,
            claim_id=request.claim_id,
            consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            execution_authorization_decision_fingerprint=
                request.execution_authorization_decision_fingerprint,
            stage63_claim_fingerprint=request.stage63_claim_fingerprint,
            stage64_envelope_fingerprint=request.stage64_envelope_fingerprint,
            stage65_handoff_receipt_fingerprint=
                request.stage65_handoff_receipt_fingerprint,
            stage66_scheduling_request_fingerprint=
                request.stage66_scheduling_request_fingerprint,
            stage66_scheduling_decision_fingerprint=
                request.stage66_scheduling_decision_fingerprint,
            stage67_scheduling_consumption_request_fingerprint=
                request.stage67_scheduling_consumption_request_fingerprint,
            stage67_scheduling_consumption_claim_fingerprint=
                request.stage67_scheduling_consumption_claim_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
        )
        if request.scheduling_scope != expected_scope:
            fail("scheduling_scope_verified", "SCHEDULING_SCOPE_MISMATCH")

        if not all(
            (
                getattr(freeze_validation, "valid", False),
                getattr(freeze_validation, "activation_gate", None)
                == "controlled_runtime_preparation_frozen",
                getattr(freeze_validation, "frozen_file_count", None) == 16,
                getattr(freeze_validation, "public_api_count", None) == 41,
                getattr(freeze_validation, "invariant_count", None) == 49,
            )
        ):
            fail("freeze_gate_verified", "FREEZE_GATE_INVALID")

        plan_ok = all(
            (
                getattr(execution_plan, "schema_name", None)
                == "ntpe.controlled_runtime_execution_plan",
                getattr(execution_plan, "status", None)
                in ("planned_not_executed", "planned_with_warnings"),
                not getattr(execution_plan, "execution_started", True),
                not getattr(execution_plan, "execution_completed", True),
                getattr(execution_plan, "provider_requests_executed", -1) == 0,
                getattr(
                    execution_plan,
                    "translation_executions_completed",
                    -1,
                )
                == 0,
                getattr(execution_plan, "execution_plan_fingerprint", None)
                == request.execution_plan_fingerprint,
                tuple(
                    getattr(
                        execution_plan,
                        "selected_adapter_unit_indices",
                        (),
                    )
                )
                == (request.selected_adapter_index,),
                getattr(
                    getattr(execution_plan, "policy", None),
                    "maximum_total_provider_requests",
                    None,
                )
                == 1,
                all(
                    getattr(step, "planned_provider_request_limit", None) == 1
                    and getattr(step, "planned_retry_limit", None) == 0
                    and getattr(step, "planned_fallback_limit", None) == 0
                    and getattr(step, "runtime_attempt_count", None) == 0
                    and getattr(step, "provider_request_count", None) == 0
                    and not getattr(step, "translation_result_attached", True)
                    for step in getattr(execution_plan, "steps", ())
                ),
            )
        )
        if not plan_ok:
            fail("execution_plan_verified", "EXECUTION_PLAN_INVALID")

        auth_ok = all(
            (
                getattr(authorization_request, "request_fingerprint", None)
                == getattr(
                    authorization_decision,
                    "authorization_request_fingerprint",
                    None,
                ),
                getattr(authorization_decision, "decision_fingerprint", None)
                == request.execution_authorization_decision_fingerprint,
                getattr(authorization_decision, "authorization_id", None)
                == request.authorization_id,
                getattr(authorization_decision, "authorized", False),
                not getattr(
                    authorization_decision,
                    "authorization_reusable",
                    True,
                ),
                getattr(authorization_result, "status", None)
                == "authorized_not_executed",
            )
        )
        if not auth_ok:
            fail("execution_authorization_verified", "AUTHORIZATION_INVALID")

        try:
            stage62_check = verify_consumption_record(
                stage62_record,
                request_fingerprint=getattr(
                    stage62_request,
                    "request_fingerprint",
                    "",
                ),
                authorization_id=request.authorization_id,
                authorization_request_fingerprint=getattr(
                    authorization_request,
                    "request_fingerprint",
                    "",
                ),
                authorization_decision_fingerprint=
                    request.execution_authorization_decision_fingerprint,
                execution_plan_fingerprint=request.execution_plan_fingerprint,
                adapter_index=request.selected_adapter_index,
                unit_count=1,
            )
            stage62_ok = (
                stage62_check.valid
                and getattr(stage62_result, "status", None)
                == "consumption_prepared_not_executed"
            )
        except Exception:
            stage62_ok = False
        if not stage62_ok:
            fail("stage62_verified", "STAGE62_INVALID")

        try:
            stage63_check = verify_atomic_consumption_claim(
                stage63_claim,
                request=stage63_claim_request,
                stage62_request=stage62_request,
                stage62_record=stage62_record,
                authorization_request=authorization_request,
                authorization_decision=authorization_decision,
                execution_plan=execution_plan,
            )
            stage63_ok = (
                stage63_check.valid
                and getattr(stage63_result, "status", None)
                == "durably_consumed_not_executed"
            )
        except Exception:
            stage63_ok = False
        if not stage63_ok:
            fail("stage63_claim_verified", "STAGE63_INVALID")

        try:
            stage64_check = verify_execution_envelope(stage64_envelope)
            stage64_ok = all(
                (
                    getattr(stage64_check, "status", None)
                    == "runtime_handoff_prepared_not_executed",
                    getattr(stage64_result, "status", None)
                    == "runtime_handoff_prepared_not_executed",
                    getattr(stage64_result, "envelope", None)
                    == stage64_envelope,
                )
            )
        except Exception:
            stage64_ok = False
        if not stage64_ok:
            fail("stage64_envelope_verified", "STAGE64_INVALID")

        try:
            stage65_check = verify_runtime_handoff_receipt(
                stage65_handoff_receipt,
                request=stage65_handoff_request,
                execution_plan=execution_plan,
                authorization_request=authorization_request,
                authorization_decision=authorization_decision,
                stage62_request=stage62_request,
                stage62_record=stage62_record,
                stage63_claim_request=stage63_claim_request,
                stage63_claim=stage63_claim,
                stage64_envelope_request=stage64_envelope_request,
                stage64_envelope=stage64_envelope,
            )
            stage65_ok = (
                stage65_check.valid
                and getattr(stage65_result, "status", None)
                == "handoff_accepted_not_scheduled_not_executed"
                and getattr(stage65_result, "receipt", None)
                == stage65_handoff_receipt
            )
        except Exception:
            stage65_ok = False
        if not stage65_ok:
            fail("stage65_handoff_receipt_verified", "STAGE65_INVALID")

        try:
            stage66_check = verify_scheduling_authorization_decision(
                stage66_scheduling_decision,
                request=stage66_scheduling_request,
                execution_plan=execution_plan,
                authorization_request=authorization_request,
                authorization_decision=authorization_decision,
                stage62_request=stage62_request,
                stage62_record=stage62_record,
                stage63_claim_request=stage63_claim_request,
                stage63_claim=stage63_claim,
                stage64_envelope_request=stage64_envelope_request,
                stage64_envelope=stage64_envelope,
                stage65_handoff_request=stage65_handoff_request,
                stage65_handoff_receipt=stage65_handoff_receipt,
            )
            stage66_request_ok = (
                getattr(
                    stage66_scheduling_request,
                    "request_fingerprint",
                    None,
                )
                == request.stage66_scheduling_request_fingerprint
            )
            stage66_decision_ok = (
                stage66_check.valid
                and getattr(
                    stage66_scheduling_decision,
                    "decision_fingerprint",
                    None,
                )
                == request.stage66_scheduling_decision_fingerprint
            )
            stage66_result_ok = all(
                (
                    getattr(stage66_scheduling_result, "status", None)
                    == "scheduling_authorized_not_consumed_not_scheduled",
                    getattr(stage66_scheduling_result, "decision", None)
                    == stage66_scheduling_decision,
                    getattr(
                        stage66_scheduling_result,
                        "authorizer_invoked",
                        False,
                    ),
                )
            ) and not any(
                getattr(stage66_scheduling_result, name, True)
                for name in (
                    "scheduler_invoked",
                    "queue_written",
                    "job_created",
                    "worker_started",
                    "runtime_invoked",
                    "provider_invoked",
                    "network_invoked",
                    "translation_invoked",
                    "output_written",
                    "resume_written",
                    "cache_written",
                    "retry_used",
                    "fallback_used",
                    "production_hook_invoked",
                )
            )
        except Exception:
            stage66_request_ok = False
            stage66_decision_ok = False
            stage66_result_ok = False
        if not stage66_request_ok:
            fail(
                "stage66_scheduling_request_verified",
                "STAGE66_REQUEST_INVALID",
            )
        if not stage66_decision_ok:
            fail(
                "stage66_scheduling_decision_verified",
                "STAGE66_DECISION_INVALID",
            )
        if not stage66_result_ok:
            fail("stage66_result_verified", "STAGE66_RESULT_INVALID")

        try:
            stage67_check = verify_atomic_scheduling_consumption_claim(
                stage67_scheduling_consumption_claim,
                request=stage67_scheduling_consumption_request,
                stage66_scheduling_request=stage66_scheduling_request,
                stage66_scheduling_decision=stage66_scheduling_decision,
                stage65_handoff_receipt=stage65_handoff_receipt,
                stage64_envelope=stage64_envelope,
                stage63_claim=stage63_claim,
                stage62_record=stage62_record,
                authorization_decision=authorization_decision,
                execution_plan=execution_plan,
            )
            stage67_request_ok = (
                getattr(
                    stage67_scheduling_consumption_request,
                    "request_fingerprint",
                    None,
                )
                == request.stage67_scheduling_consumption_request_fingerprint
            )
            stage67_claim_ok = (
                stage67_check.valid
                and getattr(
                    stage67_scheduling_consumption_claim,
                    "claim_fingerprint",
                    None,
                )
                == request.stage67_scheduling_consumption_claim_fingerprint
            )
            stage67_result_ok = all(
                (
                    getattr(
                        stage67_scheduling_consumption_result,
                        "status",
                        None,
                    )
                    == "scheduling_authorization_consumed_not_scheduled",
                    getattr(
                        stage67_scheduling_consumption_result,
                        "claim",
                        None,
                    )
                    == stage67_scheduling_consumption_claim,
                    getattr(
                        stage67_scheduling_consumption_result,
                        "consumer_invoked",
                        False,
                    ),
                    getattr(
                        stage67_scheduling_consumption_result,
                        "registry_read",
                        False,
                    ),
                    getattr(
                        stage67_scheduling_consumption_result,
                        "registry_written",
                        False,
                    ),
                )
            ) and not any(
                getattr(stage67_scheduling_consumption_result, name, True)
                for name in (
                    "scheduler_invoked",
                    "queue_written",
                    "job_created",
                    "worker_started",
                    "runtime_invoked",
                    "provider_invoked",
                    "network_invoked",
                    "translation_invoked",
                    "output_written",
                    "resume_written",
                    "cache_written",
                    "retry_used",
                    "fallback_used",
                    "production_hook_invoked",
                )
            )
        except Exception:
            stage67_request_ok = False
            stage67_claim_ok = False
            stage67_result_ok = False
        if not stage67_request_ok:
            fail(
                "stage67_scheduling_consumption_request_verified",
                "STAGE67_REQUEST_INVALID",
            )
        if not stage67_claim_ok:
            fail(
                "stage67_scheduling_consumption_claim_verified",
                "STAGE67_CLAIM_INVALID",
            )
        if not stage67_result_ok:
            fail("stage67_result_verified", "STAGE67_RESULT_INVALID")

        claim = stage67_scheduling_consumption_claim
        bindings = (
            (
                "scheduling_consumption_binding_verified",
                request.scheduling_consumption_id
                == getattr(claim, "scheduling_consumption_id", None),
            ),
            (
                "scheduling_authorization_binding_verified",
                request.scheduling_authorization_id
                == getattr(claim, "scheduling_authorization_id", None),
            ),
            (
                "handoff_binding_verified",
                request.handoff_id == getattr(claim, "handoff_id", None),
            ),
            (
                "execution_envelope_binding_verified",
                request.envelope_id == getattr(claim, "envelope_id", None),
            ),
            (
                "claim_binding_verified",
                request.claim_id == getattr(claim, "claim_id", None),
            ),
            (
                "authorization_binding_verified",
                request.authorization_id
                == getattr(claim, "authorization_id", None),
            ),
            (
                "adapter_index_verified",
                request.selected_adapter_index
                == getattr(claim, "selected_adapter_index", None),
            ),
            (
                "schedule_unit_verified",
                type(request.requested_schedule_unit_count) is int
                and request.requested_schedule_unit_count == 1
                and getattr(claim, "consumed_schedule_unit_count", None) == 1,
            ),
            (
                "runtime_boundary_verified",
                request.runtime_boundary_id
                == getattr(claim, "runtime_boundary_id", None)
                and request.runtime_boundary_kind
                == getattr(claim, "runtime_boundary_kind", None)
                == DEFAULT_POLICY.runtime_boundary_kind,
            ),
        )
        for flag, valid in bindings:
            if not valid:
                fail(flag, flag.upper().replace("_VERIFIED", "_MISMATCH"))

        if findings:
            if not flags["scheduling_scope_verified"]:
                status, action = "scheduling_scope_mismatch", "correct_request"
            elif not flags["runtime_boundary_verified"]:
                status, action = "runtime_boundary_mismatch", "do_not_admit"
            elif (
                not flags["stage67_scheduling_consumption_claim_verified"]
                or not flags["stage67_result_verified"]
            ):
                status, action = (
                    "scheduling_consumption_not_eligible",
                    "do_not_admit",
                )
            else:
                status, action = (
                    "upstream_contract_mismatch",
                    "rebuild_from_frozen_contract",
                )
            return self._result(
                request=request,
                scheduling_envelope=None,
                flags=flags,
                findings=findings,
                status=status,
                action=action,
            )

        pre_envelope_chain = tuple(
            getattr(claim, "upstream_fingerprint_chain", ())
        ) + (request.request_fingerprint,)
        try:
            scheduling_envelope = ControlledRuntimeSchedulingEnvelope(
                scheduling_envelope_id=request.scheduling_envelope_id,
                scheduling_consumption_id=request.scheduling_consumption_id,
                scheduling_authorization_id=request.scheduling_authorization_id,
                handoff_id=request.handoff_id,
                envelope_id=request.envelope_id,
                claim_id=request.claim_id,
                consumption_id=request.consumption_id,
                authorization_id=request.authorization_id,
                execution_plan_fingerprint=
                    request.execution_plan_fingerprint,
                execution_authorization_decision_fingerprint=
                    request.execution_authorization_decision_fingerprint,
                stage63_claim_fingerprint=request.stage63_claim_fingerprint,
                stage64_envelope_fingerprint=
                    request.stage64_envelope_fingerprint,
                stage65_handoff_receipt_fingerprint=
                    request.stage65_handoff_receipt_fingerprint,
                stage66_scheduling_request_fingerprint=
                    request.stage66_scheduling_request_fingerprint,
                stage66_scheduling_decision_fingerprint=
                    request.stage66_scheduling_decision_fingerprint,
                stage67_scheduling_consumption_request_fingerprint=
                    request.stage67_scheduling_consumption_request_fingerprint,
                stage67_scheduling_consumption_claim_fingerprint=
                    request.stage67_scheduling_consumption_claim_fingerprint,
                selected_adapter_index=request.selected_adapter_index,
                schedule_unit_count=1,
                runtime_boundary_id=request.runtime_boundary_id,
                runtime_boundary_kind=request.runtime_boundary_kind,
                authorization_consumed=True,
                authorization_reusable=False,
                durable_reuse_prevention_established=True,
                persistent_registry_written=True,
                runtime_handoff_prepared=True,
                runtime_handoff_completed=True,
                runtime_boundary_accepted=True,
                scheduling_authorization_requested=True,
                scheduling_authorized=True,
                scheduling_authorization_consumed=True,
                scheduling_authorization_reusable=False,
                schedule_once=True,
                durable_scheduling_reuse_prevention_established=True,
                persistent_scheduling_registry_written=True,
                scheduling_envelope_prepared=True,
                scheduling_envelope_consumed=False,
                scheduling_envelope_reusable=False,
                queue_admission_authorized=False,
                runtime_execution_scheduled=False,
                queue_record_created=False,
                job_record_created=False,
                worker_started=False,
                execution_started=False,
                execution_completed=False,
                runtime_execution_enabled=False,
                provider_execution_enabled=False,
                network_execution_enabled=False,
                translation_execution_enabled=False,
                output_write_enabled=False,
                resume_write_enabled=False,
                cache_write_enabled=False,
                retry_enabled=False,
                fallback_enabled=False,
                production_hook_enabled=False,
                envelope_state=SUCCESS_STATUS,
                upstream_fingerprint_chain=pre_envelope_chain,
                scheduling_envelope_request_fingerprint=
                    request.request_fingerprint,
            )
        except (TypeError, ValueError):
            flags["scheduling_consumption_binding_verified"] = False
            return self._result(
                request=request,
                scheduling_envelope=None,
                flags=flags,
                findings=[_finding("ENVELOPE_CONSTRUCTION_FAILED")],
                status="verification_failed",
                action="manual_integrity_review",
            )

        verification = verify_controlled_runtime_scheduling_envelope(
            scheduling_envelope,
            request=request,
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
        if not verification.valid:
            flags["scheduling_consumption_binding_verified"] = False
            return self._result(
                request=request,
                scheduling_envelope=None,
                flags=flags,
                findings=[_finding("ENVELOPE_VERIFICATION_FAILED")],
                status="verification_failed",
                action="manual_integrity_review",
            )
        return self._result(
            request=request,
            scheduling_envelope=scheduling_envelope,
            flags=flags,
            findings=[],
            status=SUCCESS_STATUS,
            action=SUCCESS_ACTION,
        )

    @staticmethod
    def _result(
        *,
        request: ControlledRuntimeSchedulingEnvelopeRequest,
        scheduling_envelope: ControlledRuntimeSchedulingEnvelope | None,
        flags: dict[str, bool],
        findings: list[ControlledRuntimeSchedulingEnvelopeFinding],
        status: str,
        action: str,
    ) -> ControlledRuntimeSchedulingEnvelopeResult:
        values: dict[str, Any] = {name: flags[name] for name in _FLAG_NAMES}
        return ControlledRuntimeSchedulingEnvelopeResult(
            request=request,
            scheduling_envelope=scheduling_envelope,
            policy_findings=tuple(findings),
            status=status,
            recommended_action=action,
            builder_invoked=True,
            **values,
        )
