"""Fail-closed Stage 6.7 consumer: consume authorization, never schedule."""

from __future__ import annotations

import pathlib
from typing import Any

from core.controlled_runtime_atomic_authorization_consumption.verification import (
    verify_atomic_consumption_claim,
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

from .errors import (
    AtomicSchedulingConsumptionAlreadyConsumedError,
    AtomicSchedulingConsumptionError,
)
from .models import (
    AtomicSchedulingAuthorizationConsumptionClaim,
    AtomicSchedulingAuthorizationConsumptionRequest,
    AtomicSchedulingAuthorizationConsumptionResult,
    AtomicSchedulingConsumptionFinding,
    canonical_sha256,
)
from .policy import DEFAULT_POLICY, SUCCESS_ACTION, SUCCESS_STATUS, exact_consumption_scope
from .registry import AtomicSchedulingAuthorizationConsumptionRegistry
from .verification import verify_atomic_scheduling_consumption_claim


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
    "authorization_binding_verified",
    "claim_binding_verified",
    "envelope_binding_verified",
    "handoff_binding_verified",
    "scheduling_authorization_binding_verified",
    "adapter_index_verified",
    "schedule_unit_verified",
    "runtime_boundary_verified",
    "consumption_scope_verified",
    "registry_namespace_verified",
    "registry_path_verified",
    "registry_write_verified",
    "durable_reuse_prevention_verified",
)


def _finding(code: str, field: str = "", message: str = "") -> AtomicSchedulingConsumptionFinding:
    return AtomicSchedulingConsumptionFinding(
        code=code,
        severity="blocking",
        message=message or code.replace("_", " ").lower(),
        field=field,
    )


class AtomicSchedulingAuthorizationConsumer:
    """Atomically consumes one authentic Stage 6.6 decision."""

    __slots__ = ("_policy",)

    def __init__(self, *, policy=DEFAULT_POLICY) -> None:
        if policy != DEFAULT_POLICY:
            raise ValueError("Stage 6.7 policy may not be changed")
        object.__setattr__(self, "_policy", policy)

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, name):
            raise AttributeError("consumer state is immutable")
        object.__setattr__(self, name, value)

    def consume(
        self,
        request: AtomicSchedulingAuthorizationConsumptionRequest,
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
        allowed_root: str | pathlib.Path,
        database_path: str | pathlib.Path,
    ) -> AtomicSchedulingAuthorizationConsumptionResult:
        if not isinstance(
            request, AtomicSchedulingAuthorizationConsumptionRequest
        ):
            raise TypeError("request must be Stage 6.7 consumption request")

        flags = {name: True for name in _FLAG_NAMES}
        findings: list[AtomicSchedulingConsumptionFinding] = []

        def fail(flag: str, code: str, field: str = "") -> None:
            flags[flag] = False
            findings.append(_finding(code, field))

        if request.request_fingerprint != canonical_sha256(
            request._fingerprint_payload()
        ):
            fail("consumption_scope_verified", "REQUEST_FINGERPRINT_MISMATCH")

        expected_scope = exact_consumption_scope(
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
            selected_adapter_index=request.selected_adapter_index,
            runtime_boundary_id=request.runtime_boundary_id,
            runtime_boundary_kind=request.runtime_boundary_kind,
        )
        if request.consumption_scope != expected_scope:
            fail("consumption_scope_verified", "CONSUMPTION_SCOPE_MISMATCH")
        if request.registry_namespace != DEFAULT_POLICY.registry_namespace:
            fail("registry_namespace_verified", "REGISTRY_NAMESPACE_MISMATCH")

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
            getattr(plan, "execution_plan_fingerprint", None)
            == request.execution_plan_fingerprint,
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
            not getattr(authorization_decision, "authorization_reusable", True),
            getattr(authorization_decision, "status", None)
            == "authorized_not_executed",
            getattr(authorization_result, "status", None)
            == "authorized_not_executed",
        ))
        if not auth_ok:
            fail("execution_authorization_verified", "AUTHORIZATION_INVALID")

        try:
            stage62_check = verify_consumption_record(
                stage62_record,
                request_fingerprint=getattr(
                    stage62_request, "request_fingerprint", ""
                ),
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
            stage64_ok = all((
                getattr(stage64_check, "status", None)
                == "runtime_handoff_prepared_not_executed",
                getattr(stage64_result, "status", None)
                == "runtime_handoff_prepared_not_executed",
                getattr(stage64_result, "envelope", None) == stage64_envelope,
                getattr(stage64_envelope_request, "request_fingerprint", None)
                == getattr(
                    stage64_envelope,
                    "envelope_request_fingerprint",
                    None,
                ),
            ))
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
            stage65_ok = all((
                stage65_check.valid,
                getattr(stage65_result, "status", None)
                == "handoff_accepted_not_scheduled_not_executed",
                getattr(stage65_result, "request", None)
                == stage65_handoff_request,
                getattr(stage65_result, "receipt", None)
                == stage65_handoff_receipt,
                getattr(stage65_result, "runtime_boundary_invoked", False),
            )) and not any(
                getattr(stage65_result, name, True)
                for name in (
                    "runtime_scheduled",
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
            stage66_request_ok = all((
                getattr(
                    stage66_scheduling_request, "request_fingerprint", None
                ) == request.stage66_scheduling_request_fingerprint,
                getattr(
                    stage66_scheduling_result, "request", None
                ) == stage66_scheduling_request,
            ))
            stage66_decision_ok = all((
                stage66_check.valid,
                getattr(
                    stage66_scheduling_decision, "decision_fingerprint", None
                ) == request.stage66_scheduling_decision_fingerprint,
                getattr(
                    stage66_scheduling_result, "decision", None
                ) == stage66_scheduling_decision,
            ))
            stage66_result_ok = all((
                getattr(stage66_scheduling_result, "status", None)
                == "scheduling_authorized_not_consumed_not_scheduled",
                getattr(stage66_scheduling_result, "recommended_action", None)
                == "retain_for_atomic_scheduling_authorization_consumption",
                getattr(stage66_scheduling_result, "authorizer_invoked", False),
            )) and not any(
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
            fail("stage66_scheduling_request_verified", "STAGE66_REQUEST_INVALID")
        if not stage66_decision_ok:
            fail("stage66_scheduling_decision_verified", "STAGE66_DECISION_INVALID")
        if not stage66_result_ok:
            fail("stage66_result_verified", "STAGE66_RESULT_INVALID")

        decision = stage66_scheduling_decision
        binding_checks = (
            (
                "scheduling_authorization_binding_verified",
                request.scheduling_authorization_id
                == getattr(decision, "scheduling_authorization_id", None),
            ),
            (
                "handoff_binding_verified",
                request.handoff_id == getattr(decision, "handoff_id", None),
            ),
            (
                "envelope_binding_verified",
                request.envelope_id == getattr(decision, "envelope_id", None),
            ),
            (
                "claim_binding_verified",
                request.claim_id == getattr(decision, "claim_id", None),
            ),
            (
                "authorization_binding_verified",
                request.authorization_id
                == getattr(decision, "authorization_id", None),
            ),
            (
                "adapter_index_verified",
                request.selected_adapter_index
                == getattr(decision, "selected_adapter_index", None),
            ),
            (
                "schedule_unit_verified",
                type(request.requested_schedule_unit_count) is int
                and request.requested_schedule_unit_count == 1
                and getattr(decision, "authorized_schedule_unit_count", None)
                == 1,
            ),
            (
                "runtime_boundary_verified",
                request.runtime_boundary_id
                == getattr(decision, "runtime_boundary_id", None)
                and request.runtime_boundary_kind
                == getattr(decision, "runtime_boundary_kind", None)
                == DEFAULT_POLICY.runtime_boundary_kind,
            ),
        )
        for flag, valid in binding_checks:
            if not valid:
                fail(flag, flag.upper().replace("_VERIFIED", "_MISMATCH"))

        fingerprint_bindings = (
            (
                request.execution_plan_fingerprint,
                getattr(decision, "execution_plan_fingerprint", None),
                "execution_plan_verified",
                "PLAN_BINDING_MISMATCH",
            ),
            (
                request.execution_authorization_decision_fingerprint,
                getattr(
                    decision,
                    "execution_authorization_decision_fingerprint",
                    None,
                ),
                "authorization_binding_verified",
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
            ),
            (
                request.stage63_claim_fingerprint,
                getattr(decision, "stage63_claim_fingerprint", None),
                "claim_binding_verified",
                "STAGE63_FINGERPRINT_MISMATCH",
            ),
            (
                request.stage64_envelope_fingerprint,
                getattr(decision, "stage64_envelope_fingerprint", None),
                "envelope_binding_verified",
                "STAGE64_FINGERPRINT_MISMATCH",
            ),
            (
                request.stage65_handoff_receipt_fingerprint,
                getattr(
                    decision,
                    "stage65_handoff_receipt_fingerprint",
                    None,
                ),
                "handoff_binding_verified",
                "STAGE65_FINGERPRINT_MISMATCH",
            ),
        )
        for expected, observed, flag, code in fingerprint_bindings:
            if expected != observed:
                fail(flag, code)

        state_ok = all((
            getattr(decision, "authorization_consumed", False),
            not getattr(decision, "authorization_reusable", True),
            getattr(decision, "durable_reuse_prevention_established", False),
            getattr(decision, "persistent_registry_written", False),
            getattr(decision, "runtime_handoff_prepared", False),
            getattr(decision, "runtime_handoff_completed", False),
            getattr(decision, "runtime_boundary_accepted", False),
            getattr(decision, "scheduling_authorization_requested", False),
            getattr(decision, "scheduling_authorized", False),
            not getattr(decision, "scheduling_authorization_consumed", True),
            not getattr(decision, "scheduling_authorization_reusable", True),
            getattr(decision, "schedule_once", False),
            not getattr(decision, "runtime_execution_scheduled", True),
            not getattr(decision, "queue_record_created", True),
            not getattr(decision, "job_record_created", True),
            not getattr(decision, "worker_started", True),
            not getattr(decision, "execution_started", True),
            not getattr(decision, "execution_completed", True),
        )) and not any(
            getattr(decision, name, True)
            for name in (
                "runtime_execution_enabled",
                "provider_execution_enabled",
                "network_execution_enabled",
                "translation_execution_enabled",
                "output_write_enabled",
                "resume_write_enabled",
                "cache_write_enabled",
                "retry_enabled",
                "fallback_enabled",
                "production_hook_enabled",
            )
        )
        if not state_ok:
            fail(
                "scheduling_authorization_binding_verified",
                "SCHEDULING_AUTHORIZATION_NOT_ELIGIBLE",
            )

        if findings:
            if not flags["consumption_scope_verified"]:
                status, action = "consumption_scope_mismatch", "correct_request"
            elif not flags["registry_namespace_verified"]:
                status, action = "invalid_request", "correct_request"
            elif not flags["runtime_boundary_verified"]:
                status, action = "runtime_boundary_mismatch", "do_not_schedule"
            else:
                status, action = (
                    "upstream_contract_mismatch",
                    "rebuild_from_frozen_contract",
                )
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status=status,
                action=action,
            )

        try:
            registry = AtomicSchedulingAuthorizationConsumptionRegistry(
                database_path, allowed_root=allowed_root
            )
        except AtomicSchedulingConsumptionError as exc:
            flags["registry_path_verified"] = False
            flags["registry_write_verified"] = False
            flags["durable_reuse_prevention_verified"] = False
            findings.append(_finding("REGISTRY_PATH_INVALID", message=str(exc)))
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status="registry_error",
                action="manual_integrity_review",
            )

        upstream_chain = tuple(
            getattr(decision, "upstream_fingerprint_chain", ())
        ) + (request.request_fingerprint,)
        try:
            claim = AtomicSchedulingAuthorizationConsumptionClaim(
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
                stage64_envelope_fingerprint=
                    request.stage64_envelope_fingerprint,
                stage65_handoff_receipt_fingerprint=
                    request.stage65_handoff_receipt_fingerprint,
                stage66_scheduling_request_fingerprint=
                    request.stage66_scheduling_request_fingerprint,
                stage66_scheduling_decision_fingerprint=
                    request.stage66_scheduling_decision_fingerprint,
                selected_adapter_index=request.selected_adapter_index,
                consumed_schedule_unit_count=1,
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
                claim_state=SUCCESS_STATUS,
                upstream_fingerprint_chain=upstream_chain,
                scheduling_consumption_request_fingerprint=
                    request.request_fingerprint,
            )
        except (TypeError, ValueError) as exc:
            flags["registry_write_verified"] = False
            flags["durable_reuse_prevention_verified"] = False
            findings.append(_finding("CLAIM_CONSTRUCTION_FAILED", message=str(exc)))
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status="verification_failed",
                action="manual_integrity_review",
            )

        try:
            stored_claim = registry.claim(request, claim)
        except AtomicSchedulingConsumptionAlreadyConsumedError as exc:
            flags["registry_write_verified"] = False
            flags["durable_reuse_prevention_verified"] = False
            findings.append(_finding("ALREADY_CONSUMED", message=str(exc)))
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status="already_consumed",
                action="reject_replay",
                registry_read=True,
            )
        except AtomicSchedulingConsumptionError as exc:
            flags["registry_write_verified"] = False
            flags["durable_reuse_prevention_verified"] = False
            findings.append(_finding("REGISTRY_ERROR", message=str(exc)))
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status="registry_error",
                action="manual_integrity_review",
                registry_read=True,
            )

        verification = verify_atomic_scheduling_consumption_claim(
            stored_claim,
            request=request,
            stage66_scheduling_request=stage66_scheduling_request,
            stage66_scheduling_decision=stage66_scheduling_decision,
            stage65_handoff_receipt=stage65_handoff_receipt,
            stage64_envelope=stage64_envelope,
            stage63_claim=stage63_claim,
            stage62_record=stage62_record,
            authorization_decision=authorization_decision,
            execution_plan=execution_plan,
        )
        if not verification.valid:
            flags["registry_write_verified"] = False
            flags["durable_reuse_prevention_verified"] = False
            findings.append(
                _finding(
                    "COMMITTED_CLAIM_VERIFICATION_FAILED",
                    message=",".join(verification.reason_codes),
                )
            )
            return self._result(
                request=request,
                claim=None,
                flags=flags,
                findings=findings,
                status="verification_failed",
                action="manual_integrity_review",
                registry_read=True,
                registry_written=True,
            )

        return self._result(
            request=request,
            claim=stored_claim,
            flags=flags,
            findings=findings,
            status=SUCCESS_STATUS,
            action=SUCCESS_ACTION,
            registry_read=True,
            registry_written=True,
        )

    @staticmethod
    def _result(
        *,
        request: AtomicSchedulingAuthorizationConsumptionRequest,
        claim: AtomicSchedulingAuthorizationConsumptionClaim | None,
        flags: dict[str, bool],
        findings: list[AtomicSchedulingConsumptionFinding],
        status: str,
        action: str,
        registry_read: bool = False,
        registry_written: bool = False,
    ) -> AtomicSchedulingAuthorizationConsumptionResult:
        values: dict[str, Any] = {name: flags[name] for name in _FLAG_NAMES}
        return AtomicSchedulingAuthorizationConsumptionResult(
            request=request,
            claim=claim,
            policy_findings=tuple(findings),
            status=status,
            recommended_action=action,
            consumer_invoked=True,
            registry_read=registry_read,
            registry_written=registry_written,
            **values,
        )