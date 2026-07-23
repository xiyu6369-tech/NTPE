from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from typing import Callable

from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlan,
    ControlledRuntimeExecutionSourceReference,
    ControlledRuntimePreparationFreezeMetadata,
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_execution_plan.policy import (
    DEFAULT_POLICY as PLAN_POLICY,
    FINDING_MESSAGES as PLAN_FINDING_MESSAGES,
    FINDING_SEVERITIES as PLAN_FINDING_SEVERITIES,
)

from .errors import InvalidControlledRuntimeExecutionAuthorizationInputError
from .models import (
    ControlledRuntimeExecutionAuthorizationDecision,
    ControlledRuntimeExecutionAuthorizationFinding,
    ControlledRuntimeExecutionAuthorizationRequest,
    ControlledRuntimeExecutionAuthorizationResult,
)
from .policy import (
    AUTHORIZED_STATUS,
    CORRECT_ACTION,
    DECISION_SCHEMA_NAME,
    DECISION_SCHEMA_VERSION,
    DEFAULT_POLICY,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    FROZEN_ACTIVATION_GATE,
    FROZEN_COMPONENT,
    FROZEN_CONTRACT_MISMATCH_STATUS,
    FROZEN_FAILURE_CODES,
    FROZEN_VERSION,
    INVALID_REQUEST_STATUS,
    PLAN_ACTION,
    PLAN_ACTIVATION_GATE,
    PLAN_SCHEMA_NAME,
    PLAN_SCHEMA_VERSION,
    PLAN_STATUSES,
    PLAN_STRATEGY,
    REBUILD_ACTION,
    REJECT_ACTION,
    REJECTED_STATUS,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RETAIN_ACTION,
    STEP_STATUS,
    ControlledRuntimeExecutionAuthorizationPolicy,
    exact_authorization_scope,
)


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_AUTHORIZATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_INVALID_REQUEST_CODES = frozenset(
    {
        "REQUEST_SCHEMA_MISMATCH",
        "REQUEST_FINGERPRINT_MISMATCH",
        "AUTHORIZATION_ID_INVALID",
        "CALLER_CONFIRMATION_REQUIRED",
        "AUTHORIZATION_SCOPE_MISMATCH",
        "PURPOSE_INVALID",
        "REQUEST_FIELD_TYPE_INVALID",
    }
)


class _FindingCollector:
    def __init__(self) -> None:
        self._items: dict[str, ControlledRuntimeExecutionAuthorizationFinding] = {}

    def add(
        self,
        code: str,
        *,
        field: str,
        expected: str | int | bool | None = None,
        observed: str | int | bool | None = None,
    ) -> None:
        self._items.setdefault(
            code,
            ControlledRuntimeExecutionAuthorizationFinding(
                code=code,
                severity=FINDING_SEVERITIES[code],
                message=FINDING_MESSAGES[code],
                field=field,
                expected=expected,
                observed=observed,
            ),
        )

    def ordered(self) -> tuple[ControlledRuntimeExecutionAuthorizationFinding, ...]:
        return tuple(
            sorted(self._items.values(), key=lambda item: FINDING_ORDER[item.code])
        )


class ControlledRuntimeExecutionAuthorizer:
    """Record one plan-bound authorization decision without executing work."""

    def __init__(
        self,
        policy: ControlledRuntimeExecutionAuthorizationPolicy | None = None,
        *,
        freeze_validator: Callable[[], object] | None = None,
        freeze_metadata_provider: (
            Callable[[], ControlledRuntimePreparationFreezeMetadata] | None
        ) = None,
    ) -> None:
        selected = DEFAULT_POLICY if policy is None else policy
        if not isinstance(selected, ControlledRuntimeExecutionAuthorizationPolicy):
            raise InvalidControlledRuntimeExecutionAuthorizationInputError(
                "policy must be a ControlledRuntimeExecutionAuthorizationPolicy"
            )
        if selected != DEFAULT_POLICY:
            raise InvalidControlledRuntimeExecutionAuthorizationInputError(
                "authorization policy cannot relax or alter the Stage 6.1 boundary"
            )
        self._policy = selected
        self._freeze_validator = (
            validate_controlled_runtime_preparation_freeze
            if freeze_validator is None
            else freeze_validator
        )
        self._freeze_metadata_provider = (
            get_controlled_runtime_preparation_freeze_metadata
            if freeze_metadata_provider is None
            else freeze_metadata_provider
        )

    def authorize(
        self,
        *,
        request: ControlledRuntimeExecutionAuthorizationRequest,
        execution_plan: ControlledRuntimeExecutionPlan,
        freeze_metadata: ControlledRuntimePreparationFreezeMetadata | None,
    ) -> ControlledRuntimeExecutionAuthorizationResult:
        if not isinstance(request, ControlledRuntimeExecutionAuthorizationRequest):
            raise InvalidControlledRuntimeExecutionAuthorizationInputError(
                "request must be a ControlledRuntimeExecutionAuthorizationRequest"
            )

        findings = _FindingCollector()
        try:
            freeze_verified = self._verify_freeze(freeze_metadata, findings)
        except Exception:
            freeze_verified = False
            findings.add(
                "FREEZE_VALIDATION_FAILED",
                field="freeze_metadata",
                expected="well_formed_stage_5_4_metadata",
                observed="malformed",
            )
        try:
            plan_verified = self._verify_plan(execution_plan, findings)
        except Exception:
            plan_verified = False
            findings.add(
                "EXECUTION_PLAN_STATE_INVALID",
                field="execution_plan",
                expected="well_formed_frozen_plan",
                observed="malformed",
            )
        try:
            self._verify_request(request, execution_plan, findings)
        except Exception:
            findings.add(
                "REQUEST_FIELD_TYPE_INVALID",
                field="request_or_execution_plan",
                expected="well_formed_immutable_values",
                observed="malformed",
            )
        ordered = findings.ordered()
        blocking_codes = tuple(
            finding.code
            for finding in ordered
            if finding.severity in {"error", "blocking"}
        )
        authorized = not blocking_codes
        if authorized:
            for code, field in (
                ("AUTHORIZATION_RECORDED_NOT_EXECUTED", "authorized"),
                ("EXACT_EXECUTION_PLAN_BOUND", "execution_plan_fingerprint"),
                ("EXACT_ADAPTER_INDEX_BOUND", "selected_adapter_index"),
                ("ONE_TIME_NON_REUSABLE_AUTHORIZATION", "authorization_reusable"),
            ):
                findings.add(code, field=field)
            ordered = findings.ordered()

        status, action = self._status_and_action(blocking_codes)
        decision = self._make_decision(
            request=request,
            plan=execution_plan,
            authorized=authorized,
            status=status,
            reason_codes=tuple(item.code for item in ordered),
        )
        result_fingerprint = _sha256_payload(
            {
                "authorization_request_fingerprint": request.request_fingerprint,
                "authorization_decision_fingerprint": decision.decision_fingerprint,
                "execution_plan_fingerprint_verified": plan_verified,
                "freeze_gate_verified": freeze_verified,
                "policy_finding_codes": [item.code for item in ordered],
                "status": status,
                "recommended_action": action,
                "boundary_counters": _zero_boundary_counters(),
            }
        )
        return ControlledRuntimeExecutionAuthorizationResult(
            request=request,
            decision=decision,
            execution_plan_fingerprint_verified=plan_verified,
            freeze_gate_verified=freeze_verified,
            policy_findings=ordered,
            status=status,
            recommended_action=action,
            runtime_invoked=False,
            provider_invoked=False,
            network_invoked=False,
            translation_invoked=False,
            output_written=False,
            resume_written=False,
            cache_written=False,
            retry_used=False,
            fallback_used=False,
            production_hook_invoked=False,
            result_fingerprint=result_fingerprint,
        )

    def _verify_freeze(
        self,
        supplied: ControlledRuntimePreparationFreezeMetadata | None,
        findings: _FindingCollector,
    ) -> bool:
        if supplied is None:
            findings.add(
                "FREEZE_METADATA_MISSING",
                field="freeze_metadata",
                expected=FROZEN_ACTIVATION_GATE,
                observed=None,
            )
            return False
        if not isinstance(supplied, ControlledRuntimePreparationFreezeMetadata):
            findings.add(
                "FREEZE_METADATA_TYPE_INVALID",
                field="freeze_metadata",
                expected="ControlledRuntimePreparationFreezeMetadata",
                observed=type(supplied).__name__,
            )
            return False
        try:
            validation = self._freeze_validator()
            expected = self._freeze_metadata_provider()
        except Exception:
            findings.add(
                "FREEZE_VALIDATION_FAILED",
                field="freeze_metadata",
                expected=True,
                observed=False,
            )
            return False
        if getattr(validation, "valid", False) is not True:
            findings.add(
                "FREEZE_VALIDATION_FAILED",
                field="freeze_validation.valid",
                expected=True,
                observed=getattr(validation, "valid", None),
            )
        if supplied != expected:
            findings.add(
                "FREEZE_METADATA_MISMATCH",
                field="freeze_metadata",
                expected="canonical_stage_5_4_metadata",
                observed="noncanonical",
            )
        if (
            supplied.activation_gate != FROZEN_ACTIVATION_GATE
            or supplied.component_name != FROZEN_COMPONENT
            or supplied.freeze_version != FROZEN_VERSION
        ):
            findings.add(
                "FREEZE_GATE_MISMATCH",
                field="freeze_metadata.activation_gate",
                expected=FROZEN_ACTIVATION_GATE,
                observed=supplied.activation_gate,
            )
        return not any(
            item.code in {
                "FREEZE_VALIDATION_FAILED",
                "FREEZE_METADATA_MISMATCH",
                "FREEZE_GATE_MISMATCH",
            }
            for item in findings.ordered()
        )

    @staticmethod
    def _verify_plan(
        plan: object,
        findings: _FindingCollector,
    ) -> bool:
        if not isinstance(plan, ControlledRuntimeExecutionPlan):
            findings.add(
                "EXECUTION_PLAN_TYPE_INVALID",
                field="execution_plan",
                expected="ControlledRuntimeExecutionPlan",
                observed=type(plan).__name__,
            )
            return False
        if (
            plan.schema_name != PLAN_SCHEMA_NAME
            or plan.schema_version != PLAN_SCHEMA_VERSION
            or plan.strategy != PLAN_STRATEGY
            or plan.activation_gate != PLAN_ACTIVATION_GATE
        ):
            findings.add(
                "EXECUTION_PLAN_SCHEMA_MISMATCH",
                field="execution_plan.schema",
                expected=f"{PLAN_SCHEMA_NAME}/{PLAN_SCHEMA_VERSION}",
                observed=f"{plan.schema_name}/{plan.schema_version}",
            )
        if plan.status not in PLAN_STATUSES or plan.action != PLAN_ACTION:
            findings.add(
                "EXECUTION_PLAN_STATE_INVALID",
                field="execution_plan.status",
                expected="planned_not_executed",
                observed=plan.status,
            )
        if (
            len(plan.steps) != 1
            or plan.planned_step_count != 1
            or len(plan.selected_adapter_unit_indices) != 1
        ):
            findings.add(
                "EXECUTION_PLAN_SCOPE_INVALID",
                field="execution_plan.steps",
                expected=1,
                observed=len(plan.steps),
            )
        if not plan.selected_adapter_unit_indices:
            findings.add(
                "EXECUTION_PLAN_SELECTION_AUTOMATIC",
                field="selected_adapter_unit_indices",
                expected="one_explicit_index",
                observed="empty",
            )

        for step in plan.steps:
            if _execution_step_fingerprint(step) != step.execution_step_fingerprint:
                findings.add(
                    "EXECUTION_STEP_FINGERPRINT_MISMATCH",
                    field="execution_step_fingerprint",
                    expected="canonical",
                    observed="mismatch",
                )
            if _sha256_text(step.text) != step.source_chunk_fingerprint:
                findings.add(
                    "EXECUTION_PLAN_TEXT_FINGERPRINT_MISMATCH",
                    field="execution_step.text",
                    expected=step.source_chunk_fingerprint,
                    observed=_sha256_text(step.text),
                )
        if plan.steps and (
            plan.steps[0].status != STEP_STATUS
            or plan.steps[0].runtime_attempt_count != 0
            or plan.steps[0].provider_request_count != 0
            or plan.steps[0].translation_result_attached is not False
        ):
            findings.add(
                "EXECUTION_PLAN_STATE_INVALID",
                field="execution_step.status",
                expected=STEP_STATUS,
                observed=plan.steps[0].status,
            )
        if plan.execution_started is not False:
            findings.add(
                "EXECUTION_PLAN_ALREADY_STARTED",
                field="execution_started",
                expected=False,
                observed=plan.execution_started,
            )
        if plan.execution_completed is not False:
            findings.add(
                "EXECUTION_PLAN_ALREADY_COMPLETED",
                field="execution_completed",
                expected=False,
                observed=plan.execution_completed,
            )
        if plan.provider_requests_executed != 0:
            findings.add(
                "PROVIDER_EXECUTION_COUNTER_NONZERO",
                field="provider_requests_executed",
                expected=0,
                observed=plan.provider_requests_executed,
            )
        if plan.translation_executions_completed != 0:
            findings.add(
                "TRANSLATION_EXECUTION_COUNTER_NONZERO",
                field="translation_executions_completed",
                expected=0,
                observed=plan.translation_executions_completed,
            )
        if not _plan_content_is_canonical(plan):
            findings.add(
                "EXECUTION_PLAN_STATE_INVALID",
                field="execution_plan.content",
                expected="canonical_stage_5_3_plan",
                observed="noncanonical",
            )
        if _plan_relaxes_capabilities(plan):
            findings.add(
                "EXECUTION_PLAN_CAPABILITY_RELAXATION",
                field="execution_plan.policy",
                expected="stage_5_3_frozen_boundary",
                observed="relaxed_or_noncanonical",
            )
        expected_fingerprint = _execution_plan_fingerprint(plan)
        if (
            not _HEX_64.fullmatch(plan.execution_plan_fingerprint)
            or plan.execution_plan_fingerprint != expected_fingerprint
        ):
            findings.add(
                "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
                field="execution_plan_fingerprint",
                expected=expected_fingerprint,
                observed=plan.execution_plan_fingerprint,
            )
        return not any(
            item.code.startswith("EXECUTION_PLAN")
            or item.code in {
                "EXECUTION_STEP_FINGERPRINT_MISMATCH",
                "PROVIDER_EXECUTION_COUNTER_NONZERO",
                "TRANSLATION_EXECUTION_COUNTER_NONZERO",
            }
            for item in findings.ordered()
        )

    @staticmethod
    def _verify_request(
        request: ControlledRuntimeExecutionAuthorizationRequest,
        plan: object,
        findings: _FindingCollector,
    ) -> None:
        if (
            request.schema_name != REQUEST_SCHEMA_NAME
            or request.schema_version != REQUEST_SCHEMA_VERSION
        ):
            findings.add(
                "REQUEST_SCHEMA_MISMATCH",
                field="request.schema",
                expected=f"{REQUEST_SCHEMA_NAME}/{REQUEST_SCHEMA_VERSION}",
                observed=f"{request.schema_name}/{request.schema_version}",
            )
        try:
            expected_request_fingerprint = _sha256_payload(
                request.fingerprint_payload()
            )
        except (TypeError, ValueError):
            expected_request_fingerprint = ""
            findings.add(
                "REQUEST_FIELD_TYPE_INVALID",
                field="request",
                expected="canonical_json_values",
                observed="malformed",
            )
        if (
            not _HEX_64.fullmatch(request.request_fingerprint)
            or request.request_fingerprint != expected_request_fingerprint
        ):
            findings.add(
                "REQUEST_FINGERPRINT_MISMATCH",
                field="request_fingerprint",
                expected=expected_request_fingerprint,
                observed=request.request_fingerprint,
            )
        if (
            not isinstance(request.authorization_id, str)
            or not _AUTHORIZATION_ID.fullmatch(request.authorization_id)
            or _UUID.fullmatch(request.authorization_id)
        ):
            findings.add(
                "AUTHORIZATION_ID_INVALID",
                field="authorization_id",
                expected="caller_supplied_reference",
                observed=_safe_observed(request.authorization_id),
            )
        if type(request.caller_confirmation) is not bool:
            findings.add(
                "REQUEST_FIELD_TYPE_INVALID",
                field="caller_confirmation",
                expected="bool",
                observed=type(request.caller_confirmation).__name__,
            )
        elif request.caller_confirmation is not True:
            findings.add(
                "CALLER_CONFIRMATION_REQUIRED",
                field="caller_confirmation",
                expected=True,
                observed=request.caller_confirmation,
            )
        if not isinstance(request.purpose, str) or not request.purpose.strip():
            findings.add(
                "PURPOSE_INVALID",
                field="purpose",
                expected="non_empty_caller_metadata",
                observed=_safe_observed(request.purpose),
            )

        if not isinstance(plan, ControlledRuntimeExecutionPlan):
            return
        selected = (
            plan.selected_adapter_unit_indices[0]
            if len(plan.selected_adapter_unit_indices) == 1
            else None
        )
        expected_scope = (
            exact_authorization_scope(plan.execution_plan_fingerprint, selected)
            if selected is not None
            else ""
        )
        if request.authorization_scope != expected_scope:
            findings.add(
                "AUTHORIZATION_SCOPE_MISMATCH",
                field="authorization_scope",
                expected=expected_scope,
                observed=_safe_observed(request.authorization_scope),
            )
        if (
            not _HEX_64.fullmatch(request.execution_plan_fingerprint)
            or request.execution_plan_fingerprint
            != plan.execution_plan_fingerprint
        ):
            findings.add(
                "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
                field="request.execution_plan_fingerprint",
                expected=plan.execution_plan_fingerprint,
                observed=request.execution_plan_fingerprint,
            )
        if (
            type(request.selected_adapter_index) is not int
            or request.selected_adapter_index != selected
        ):
            findings.add(
                "ADAPTER_INDEX_MISMATCH",
                field="selected_adapter_index",
                expected=selected,
                observed=_safe_observed(request.selected_adapter_index),
            )
        if (
            type(request.requested_unit_count) is not int
            or request.requested_unit_count != 1
            or (
                request.requested_adapter_indices
                and request.requested_adapter_indices != (selected,)
            )
        ):
            findings.add(
                "MULTIPLE_UNIT_AUTHORIZATION_REJECTED",
                field="requested_unit_count",
                expected=1,
                observed=_safe_observed(request.requested_unit_count),
            )
        expected_order = tuple(
            step.execution_step_fingerprint for step in plan.steps
        )
        if (
            request.requested_plan_step_fingerprints
            and request.requested_plan_step_fingerprints != expected_order
        ):
            findings.add(
                "PLAN_ORDER_CHANGE_REJECTED",
                field="requested_plan_step_fingerprints",
                expected="execution_plan_order",
                observed="different_order",
            )
        _require_exact_int(
            request.requested_provider_request_limit,
            1,
            "PROVIDER_REQUEST_LIMIT_INVALID",
            "requested_provider_request_limit",
            findings,
        )
        _require_exact_int(
            request.requested_translation_request_limit,
            1,
            "TRANSLATION_REQUEST_LIMIT_INVALID",
            "requested_translation_request_limit",
            findings,
        )
        for field, code in (
            ("retry_requested", "RETRY_REQUEST_REJECTED"),
            ("fallback_requested", "FALLBACK_REQUEST_REJECTED"),
            ("output_replacement_requested", "OUTPUT_REPLACEMENT_REQUEST_REJECTED"),
            ("cache_write_requested", "CACHE_WRITE_REQUEST_REJECTED"),
            ("resume_write_requested", "RESUME_WRITE_REQUEST_REJECTED"),
            (
                "production_integration_requested",
                "PRODUCTION_INTEGRATION_REQUEST_REJECTED",
            ),
        ):
            _require_exact_bool(request, field, False, code, findings)
        for field, code in (
            ("runtime_execution_requested", "RUNTIME_EXECUTION_INTENT_REQUIRED"),
            ("provider_execution_requested", "PROVIDER_EXECUTION_INTENT_REQUIRED"),
            ("network_execution_requested", "NETWORK_EXECUTION_INTENT_REQUIRED"),
            (
                "translation_execution_requested",
                "TRANSLATION_EXECUTION_INTENT_REQUIRED",
            ),
        ):
            _require_exact_bool(request, field, True, code, findings)

    @staticmethod
    def _status_and_action(
        blocking_codes: tuple[str, ...],
    ) -> tuple[str, str]:
        if not blocking_codes:
            return AUTHORIZED_STATUS, RETAIN_ACTION
        if any(code in FROZEN_FAILURE_CODES for code in blocking_codes):
            return FROZEN_CONTRACT_MISMATCH_STATUS, REBUILD_ACTION
        if any(code in _INVALID_REQUEST_CODES for code in blocking_codes):
            return INVALID_REQUEST_STATUS, CORRECT_ACTION
        return REJECTED_STATUS, REJECT_ACTION

    def _make_decision(
        self,
        *,
        request: ControlledRuntimeExecutionAuthorizationRequest,
        plan: object,
        authorized: bool,
        status: str,
        reason_codes: tuple[str, ...],
    ) -> ControlledRuntimeExecutionAuthorizationDecision:
        valid_plan = isinstance(plan, ControlledRuntimeExecutionPlan)
        source = (
            plan.source
            if valid_plan
            and isinstance(
                plan.source, ControlledRuntimeExecutionSourceReference
            )
            else None
        )
        selected_indices = (
            plan.selected_adapter_unit_indices
            if valid_plan
            and isinstance(plan.selected_adapter_unit_indices, tuple)
            else ()
        )
        selected = (
            selected_indices[0]
            if len(selected_indices) == 1
            else None
        )
        payload = {
            "schema_name": DECISION_SCHEMA_NAME,
            "schema_version": DECISION_SCHEMA_VERSION,
            "authorization_id": request.authorization_id,
            "authorized": authorized,
            "status": status,
            "reason_codes": list(reason_codes),
            "execution_package_fingerprint": (
                source.execution_package_fingerprint if source else ""
            ),
            "upstream_authorization_decision_fingerprint": (
                source.authorization_fingerprint if source else ""
            ),
            "approval_record_fingerprint": (
                source.approval_record_fingerprint if source else ""
            ),
            "runtime_submission_package_fingerprint": (
                source.runtime_submission_package_fingerprint if source else ""
            ),
            "runtime_adapter_request_fingerprint": (
                source.runtime_adapter_request_fingerprint if source else ""
            ),
            "runtime_adapter_preparation_fingerprint": (
                source.runtime_adapter_preparation_fingerprint if source else ""
            ),
            "authorization_request_fingerprint": request.request_fingerprint,
            "authorized_execution_plan_fingerprint": (
                plan.execution_plan_fingerprint if authorized and valid_plan else ""
            ),
            "authorized_adapter_index": selected if authorized else None,
            "authorized_unit_count": 1 if authorized else 0,
            "authorized_provider_request_limit": 1 if authorized else 0,
            "authorized_translation_request_limit": 1 if authorized else 0,
            "authorized_retry_limit": 0,
            "authorized_fallback_limit": 0,
            "output_replacement_authorized": False,
            "production_integration_authorized": False,
            "runtime_execution_enabled": False,
            "provider_execution_enabled": False,
            "network_execution_enabled": False,
            "translation_execution_enabled": False,
            "authorization_consumed": False,
            "authorization_reusable": False,
        }
        decision_fingerprint = _sha256_payload(payload)
        payload["reason_codes"] = reason_codes
        return ControlledRuntimeExecutionAuthorizationDecision(
            **payload,
            decision_fingerprint=decision_fingerprint,
        )


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _execution_step_fingerprint(step: object) -> str:
    return _sha256_payload(
        {
            "step_index": step.step_index,
            "adapter_unit_index": step.adapter_unit_index,
            "submission_index": step.submission_index,
            "execution_unit_index": step.execution_unit_index,
            "execution_unit_id": step.execution_unit_id,
            "source_character_start": step.source_character_start,
            "source_character_end": step.source_character_end,
            "section_indices": list(step.section_indices),
            "source_chunk_fingerprint": step.source_chunk_fingerprint,
            "execution_unit_fingerprint": step.execution_unit_fingerprint,
            "runtime_submission_unit_fingerprint": (
                step.runtime_submission_unit_fingerprint
            ),
            "runtime_adapter_unit_fingerprint": (
                step.runtime_adapter_unit_fingerprint
            ),
            "planned_provider_request_limit": (
                step.planned_provider_request_limit
            ),
            "planned_retry_limit": step.planned_retry_limit,
            "planned_fallback_limit": step.planned_fallback_limit,
            "status": step.status,
            "runtime_attempt_count": step.runtime_attempt_count,
            "provider_request_count": step.provider_request_count,
            "translation_result_attached": step.translation_result_attached,
        }
    )


def _execution_plan_fingerprint(plan: ControlledRuntimeExecutionPlan) -> str:
    return _sha256_payload(
        {
            "schema_name": plan.schema_name,
            "schema_version": plan.schema_version,
            "strategy": plan.strategy,
            "activation_gate": plan.activation_gate,
            "source": asdict(plan.source),
            "policy": asdict(plan.policy),
            "selected_adapter_unit_indices": list(
                plan.selected_adapter_unit_indices
            ),
            "step_fingerprints": [
                step.execution_step_fingerprint for step in plan.steps
            ],
            "planned_step_count": plan.planned_step_count,
            "available_adapter_unit_count": plan.available_adapter_unit_count,
            "planned_character_count": plan.planned_character_count,
            "approved_character_count": plan.approved_character_count,
            "planned_approval_coverage_ratio": (
                plan.planned_approval_coverage_ratio
            ),
            "status": plan.status,
            "action": plan.action,
            "finding_codes": [finding.code for finding in plan.findings],
            "authorization_flags": {
                "runtime_execution_authorized": (
                    plan.runtime_execution_authorized
                ),
                "provider_execution_authorized": (
                    plan.provider_execution_authorized
                ),
                "translation_execution_authorized": (
                    plan.translation_execution_authorized
                ),
            },
            "enablement_flags": {
                "runtime_execution_enabled": plan.runtime_execution_enabled,
                "provider_execution_enabled": plan.provider_execution_enabled,
                "translation_execution_enabled": (
                    plan.translation_execution_enabled
                ),
            },
            "automatic_retry_authorized": plan.automatic_retry_authorized,
            "automatic_fallback_authorized": (
                plan.automatic_fallback_authorized
            ),
            "output_replacement_authorized": (
                plan.output_replacement_authorized
            ),
            "execution_started": plan.execution_started,
            "execution_completed": plan.execution_completed,
            "provider_requests_executed": plan.provider_requests_executed,
            "translation_executions_completed": (
                plan.translation_executions_completed
            ),
        }
    )


def _plan_relaxes_capabilities(plan: ControlledRuntimeExecutionPlan) -> bool:
    if plan.policy != PLAN_POLICY:
        return True
    if (
        plan.runtime_execution_authorized is not True
        or plan.provider_execution_authorized is not True
        or plan.translation_execution_authorized is not True
    ):
        return True
    if (
        plan.runtime_execution_enabled is not False
        or plan.provider_execution_enabled is not False
        or plan.translation_execution_enabled is not False
        or plan.automatic_retry_authorized is not False
        or plan.automatic_fallback_authorized is not False
        or plan.output_replacement_authorized is not False
    ):
        return True
    if plan.steps and (
        plan.steps[0].planned_provider_request_limit != 1
        or plan.steps[0].planned_retry_limit != 0
        or plan.steps[0].planned_fallback_limit != 0
    ):
        return True
    return False


def _plan_content_is_canonical(plan: ControlledRuntimeExecutionPlan) -> bool:
    if not isinstance(plan.steps, tuple) or not isinstance(
        plan.selected_adapter_unit_indices, tuple
    ) or not isinstance(plan.findings, tuple):
        return False
    if len(plan.steps) != 1 or len(plan.selected_adapter_unit_indices) != 1:
        return False
    step = plan.steps[0]
    selected = plan.selected_adapter_unit_indices[0]
    if (
        type(selected) is not int
        or selected < 0
        or selected >= plan.available_adapter_unit_count
        or step.step_index != 0
        or step.adapter_unit_index != selected
        or step.source_character_start < 0
        or step.source_character_end - step.source_character_start != len(step.text)
        or plan.planned_step_count != 1
        or plan.planned_character_count != len(step.text)
        or plan.approved_character_count <= 0
        or plan.planned_approval_coverage_ratio
        != plan.planned_character_count / plan.approved_character_count
        or plan.reconstruct_planned_text() != step.text
        or plan.summary
        != (
            f"Single-unit execution plan prepared for adapter unit "
            f"{selected}; execution remains disabled."
        )
    ):
        return False
    expected_codes = [
        "CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED",
        "SINGLE_UNIT_EXECUTION_SCOPE",
    ]
    if plan.status == "planned_with_warnings":
        expected_codes.append("ADAPTER_WARNING_PROPAGATED")
    expected_codes.extend(
        [
            "EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED",
            "RUNTIME_EXECUTION_NOT_STARTED",
            "RUNTIME_EXECUTION_NOT_COMPLETED",
            "PROVIDER_REQUEST_COUNT_ZERO",
            "TRANSLATION_EXECUTION_COUNT_ZERO",
            "RUNTIME_EXECUTION_CAPABILITY_DISABLED",
            "PROVIDER_EXECUTION_CAPABILITY_DISABLED",
            "TRANSLATION_EXECUTION_CAPABILITY_DISABLED",
        ]
    )
    if [finding.code for finding in plan.findings] != expected_codes:
        return False
    for finding in plan.findings:
        if (
            finding.severity != PLAN_FINDING_SEVERITIES.get(finding.code)
            or finding.message != PLAN_FINDING_MESSAGES.get(finding.code)
            or finding.step_index is not None
            or finding.observed_value is not None
            or finding.required_value is not None
        ):
            return False
    return all(
        isinstance(value, str) and _HEX_64.fullmatch(value)
        for name, value in vars(plan.source).items()
        if name.endswith("_fingerprint")
    )

def _require_exact_int(
    observed: object,
    expected: int,
    code: str,
    field: str,
    findings: _FindingCollector,
) -> None:
    if type(observed) is not int or observed != expected:
        findings.add(
            code,
            field=field,
            expected=expected,
            observed=_safe_observed(observed),
        )


def _require_exact_bool(
    request: ControlledRuntimeExecutionAuthorizationRequest,
    field: str,
    expected: bool,
    code: str,
    findings: _FindingCollector,
) -> None:
    observed = getattr(request, field)
    if type(observed) is not bool:
        findings.add(
            "REQUEST_FIELD_TYPE_INVALID",
            field=field,
            expected="bool",
            observed=type(observed).__name__,
        )
    elif observed is not expected:
        findings.add(code, field=field, expected=expected, observed=observed)


def _safe_observed(value: object) -> str | int | bool | None:
    if value is None or type(value) in {str, int, bool}:
        return value
    return type(value).__name__


def _zero_boundary_counters() -> dict[str, int]:
    return {
        "runtime_execution": 0,
        "provider_execution": 0,
        "network_execution": 0,
        "translation_execution": 0,
        "output_write": 0,
        "resume_write": 0,
        "cache_write": 0,
        "retry": 0,
        "fallback": 0,
        "production_hook": 0,
    }

