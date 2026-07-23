from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import PurePosixPath, PureWindowsPath

from core.controlled_runtime_adapter import RuntimeAdapterPreparationResult
from core.controlled_runtime_adapter.policy import (
    ACTIVATION_GATE as ADAPTER_ACTIVATION_GATE,
    FINDING_MESSAGES as ADAPTER_FINDING_MESSAGES,
    FINDING_SEVERITIES as ADAPTER_FINDING_SEVERITIES,
    HOLD_ACTION as ADAPTER_HOLD_ACTION,
    PACKAGE_STATUS as ADAPTER_STATUS,
    PACKAGE_WARNING_STATUS as ADAPTER_WARNING_STATUS,
    PROFILE_NAME as ADAPTER_PROFILE_NAME,
    PROFILE_VERSION as ADAPTER_PROFILE_VERSION,
    PROHIBITED_CAPABILITIES as ADAPTER_PROHIBITED_CAPABILITIES,
    SCHEMA_NAME as ADAPTER_SCHEMA_NAME,
    SCHEMA_VERSION as ADAPTER_SCHEMA_VERSION,
    STRATEGY as ADAPTER_STRATEGY,
)

from .errors import (
    ControlledRuntimeExecutionConsistencyError,
    ControlledRuntimeExecutionInvariantError,
    ControlledRuntimeExecutionPolicyError,
    ControlledRuntimeExecutionScopeError,
    InvalidControlledRuntimeExecutionInputError,
)
from .models import (
    ControlledRuntimeExecutionFinding,
    ControlledRuntimeExecutionPlan,
    ControlledRuntimeExecutionPolicy,
    ControlledRuntimeExecutionSourceReference,
    ControlledRuntimeExecutionStep,
)
from .policy import (
    ACTIVATION_GATE,
    DEFAULT_POLICY,
    EXECUTION_MODE,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    HOLD_ACTION,
    PLAN_STATUS,
    PLAN_WARNING_STATUS,
    POLICY_NAME,
    POLICY_VERSION,
    PROHIBITED_TRUE_FIELDS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STEP_STATUS,
    STRATEGY,
)


class _FindingCollector:
    def __init__(self) -> None:
        self._items: dict[tuple[str, int | None], ControlledRuntimeExecutionFinding] = {}

    def add(
        self,
        code: str,
        *,
        step_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        self._items.setdefault(
            (code, step_index),
            ControlledRuntimeExecutionFinding(
                code=code,
                severity=FINDING_SEVERITIES[code],
                message=FINDING_MESSAGES[code],
                step_index=step_index,
                observed_value=observed_value,
                required_value=required_value,
            ),
        )

    def ordered(self) -> tuple[ControlledRuntimeExecutionFinding, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda finding: (
                    FINDING_ORDER[finding.code],
                    -1 if finding.step_index is None else finding.step_index,
                ),
            )
        )


class ControlledRuntimeExecutionPlanner:
    """Prepare one explicit immutable execution step without executing it."""

    def __init__(
        self,
        policy: ControlledRuntimeExecutionPolicy | None = None,
    ) -> None:
        selected_policy = DEFAULT_POLICY if policy is None else policy
        if not isinstance(selected_policy, ControlledRuntimeExecutionPolicy):
            raise InvalidControlledRuntimeExecutionInputError(
                "policy must be a ControlledRuntimeExecutionPolicy"
            )
        self._validate_policy_boundary(selected_policy)
        self._policy = selected_policy

    def plan(
        self,
        *,
        adapter_preparation_result: RuntimeAdapterPreparationResult,
        selected_adapter_unit_indices: tuple[int, ...] | None = None,
    ) -> ControlledRuntimeExecutionPlan:
        if not isinstance(
            adapter_preparation_result, RuntimeAdapterPreparationResult
        ):
            raise InvalidControlledRuntimeExecutionInputError(
                "adapter_preparation_result must be a RuntimeAdapterPreparationResult"
            )
        selected_index = self._validate_scope(
            adapter_preparation_result,
            selected_adapter_unit_indices,
        )
        self._validate_adapter_preparation(adapter_preparation_result)
        self._validate_policy_for_plan(adapter_preparation_result)

        request = adapter_preparation_result.request
        unit = request.units[selected_index]
        step = self._map_step(unit)
        steps = (step,)
        planned_character_count = len(step.text)
        approved_character_count = request.approved_character_count
        planned_coverage = (
            planned_character_count / approved_character_count
            if approved_character_count > 0
            else 0.0
        )
        status = (
            PLAN_WARNING_STATUS
            if request.status == ADAPTER_WARNING_STATUS
            else PLAN_STATUS
        )
        findings = self._success_findings(
            warning=request.status == ADAPTER_WARNING_STATUS
        )
        source = ControlledRuntimeExecutionSourceReference(
            source_name=_safe_name(request.source.source_name),
            source_content_fingerprint=request.source.source_content_fingerprint,
            execution_package_fingerprint=(
                request.source.execution_package_fingerprint
            ),
            authorization_fingerprint=request.source.authorization_fingerprint,
            approval_record_fingerprint=(
                request.source.approval_record_fingerprint
            ),
            runtime_submission_package_fingerprint=(
                request.source.runtime_submission_package_fingerprint
            ),
            runtime_adapter_request_fingerprint=(
                request.runtime_adapter_request_fingerprint
            ),
            runtime_adapter_preparation_fingerprint=(
                adapter_preparation_result.preparation_fingerprint
            ),
            manifest_fingerprint=request.source.manifest_fingerprint,
            segmentation_fingerprint=request.source.segmentation_fingerprint,
            chunk_plan_fingerprint=request.source.chunk_plan_fingerprint,
            preparation_fingerprint=request.source.preparation_fingerprint,
        )
        fingerprint = _plan_fingerprint(
            source=source,
            policy=self._policy,
            steps=steps,
            selected_indices=(selected_index,),
            available_count=request.adapter_unit_count,
            planned_character_count=planned_character_count,
            approved_character_count=approved_character_count,
            planned_coverage=planned_coverage,
            status=status,
            findings=findings,
            request=request,
        )
        plan = ControlledRuntimeExecutionPlan(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            strategy=STRATEGY,
            activation_gate=ACTIVATION_GATE,
            source=source,
            policy=self._policy,
            steps=steps,
            selected_adapter_unit_indices=(selected_index,),
            planned_step_count=1,
            available_adapter_unit_count=request.adapter_unit_count,
            planned_character_count=planned_character_count,
            approved_character_count=approved_character_count,
            planned_approval_coverage_ratio=planned_coverage,
            status=status,
            action=HOLD_ACTION,
            findings=findings,
            summary=(
                f"Single-unit execution plan prepared for adapter unit "
                f"{selected_index}; execution remains disabled."
            ),
            runtime_execution_authorized=request.runtime_submission_authorized,
            provider_execution_authorized=request.provider_execution_authorized,
            translation_execution_authorized=(
                request.translation_execution_authorized
            ),
            runtime_execution_enabled=self._policy.runtime_execution_enabled,
            provider_execution_enabled=self._policy.provider_execution_enabled,
            translation_execution_enabled=(
                self._policy.translation_execution_enabled
            ),
            automatic_retry_authorized=request.automatic_retry_authorized,
            automatic_fallback_authorized=(
                request.automatic_fallback_authorized
            ),
            output_replacement_authorized=(
                request.output_replacement_authorized
            ),
            execution_started=False,
            execution_completed=False,
            provider_requests_executed=0,
            translation_executions_completed=0,
            execution_plan_fingerprint=fingerprint,
        )
        if plan.reconstruct_planned_text() != unit.text:
            raise ControlledRuntimeExecutionInvariantError(
                "Execution plan does not reconstruct the selected adapter unit."
            )
        return plan

    @staticmethod
    def _validate_policy_boundary(
        policy: ControlledRuntimeExecutionPolicy,
    ) -> None:
        if (
            policy.policy_name != POLICY_NAME
            or policy.policy_version != POLICY_VERSION
            or policy.execution_mode != EXECUTION_MODE
        ):
            _raise_policy(
                "Policy identity or execution mode is not canonical."
            )
        integer_limits = (
            "maximum_units_per_execution",
            "maximum_provider_requests_per_unit",
            "maximum_total_provider_requests",
        )
        for name in integer_limits:
            value = getattr(policy, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                or value > getattr(DEFAULT_POLICY, name)
            ):
                _raise_policy(f"Policy limit {name} relaxes the Stage 5.3 boundary.")
        boolean_fields = (
            "allow_partial_scope",
            *PROHIBITED_TRUE_FIELDS,
        )
        if any(type(getattr(policy, name)) is not bool for name in boolean_fields):
            _raise_policy("Policy capability values must be booleans.")
        enabled = tuple(
            name for name in PROHIBITED_TRUE_FIELDS if getattr(policy, name)
        )
        if enabled:
            _raise_policy(
                "Policy attempts to enable prohibited behavior: "
                + ",".join(enabled)
            )

    def _validate_policy_for_plan(
        self,
        result: RuntimeAdapterPreparationResult,
    ) -> None:
        if self._policy.maximum_units_per_execution < 1:
            _raise_policy("Policy cannot plan the required single unit.")
        if (
            self._policy.maximum_provider_requests_per_unit < 1
            or self._policy.maximum_total_provider_requests < 1
        ):
            finding = _finding(
                "PROVIDER_REQUEST_LIMIT_EXCEEDED",
                observed_value=0,
                required_value=1,
            )
            raise ControlledRuntimeExecutionPolicyError(
                finding.message,
                finding=finding,
            )
        if (
            result.request.adapter_unit_count > 1
            and not self._policy.allow_partial_scope
        ):
            _raise_policy("Policy does not permit the required partial plan scope.")

    def _validate_scope(
        self,
        result: RuntimeAdapterPreparationResult,
        indices: tuple[int, ...] | None,
    ) -> int:
        if indices is None or indices == ():
            _raise_scope("EXECUTION_SCOPE_EMPTY")
        if not isinstance(indices, tuple):
            _raise_scope("EXECUTION_SCOPE_TYPE_MISMATCH")
        if len(indices) > 1:
            _raise_scope("EXECUTION_SCOPE_MULTIPLE_UNITS_REJECTED")
        index = indices[0]
        if isinstance(index, bool) or not isinstance(index, int):
            _raise_scope("EXECUTION_SCOPE_TYPE_MISMATCH")
        if index < 0 or index >= result.request.adapter_unit_count:
            _raise_scope("EXECUTION_SCOPE_OUT_OF_RANGE")
        if index >= len(result.request.units):
            _raise_scope("ADAPTER_UNIT_NOT_FOUND")
        unit = result.request.units[index]
        if unit.adapter_unit_index != index:
            _raise_scope("ADAPTER_UNIT_NOT_FOUND")
        if unit.execution_unit_index not in result.request.approved_unit_indices:
            _raise_scope("EXECUTION_SCOPE_NOT_APPROVED")
        return index

    @staticmethod
    def _validate_adapter_preparation(
        result: RuntimeAdapterPreparationResult,
    ) -> None:
        if (
            result.prepared is not True
            or result.compatible is not True
            or result.runtime_invoked is not False
            or result.provider_invoked is not False
            or result.translation_invoked is not False
        ):
            _raise_consistency(
                "ADAPTER_PREPARATION_INVALID",
                "invalid_preparation_state",
                "prepared_compatible_not_invoked",
            )
        request = result.request
        if (
            request.schema_name != ADAPTER_SCHEMA_NAME
            or request.schema_version != ADAPTER_SCHEMA_VERSION
            or request.strategy != ADAPTER_STRATEGY
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_SCHEMA_MISMATCH",
                f"{request.schema_name}:{request.schema_version}:{request.strategy}",
                f"{ADAPTER_SCHEMA_NAME}:{ADAPTER_SCHEMA_VERSION}:{ADAPTER_STRATEGY}",
            )
        if (
            request.activation_gate != ADAPTER_ACTIVATION_GATE
            or request.status not in {ADAPTER_STATUS, ADAPTER_WARNING_STATUS}
            or request.action != ADAPTER_HOLD_ACTION
            or result.status != request.status
            or result.action != request.action
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_GATE_MISMATCH",
                f"{request.activation_gate}:{request.status}:{request.action}",
                ADAPTER_ACTIVATION_GATE,
            )
        ControlledRuntimeExecutionPlanner._validate_capability_profile(result)
        ControlledRuntimeExecutionPlanner._validate_request_content(request)
        ControlledRuntimeExecutionPlanner._validate_adapter_findings(result)
        expected_request_fingerprint = _adapter_request_fingerprint(request)
        if (
            request.runtime_adapter_request_fingerprint
            != expected_request_fingerprint
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                request.runtime_adapter_request_fingerprint,
                expected_request_fingerprint,
            )
        expected_preparation_fingerprint = _adapter_preparation_fingerprint(
            result
        )
        if result.preparation_fingerprint != expected_preparation_fingerprint:
            _raise_consistency(
                "ADAPTER_PREPARATION_FINGERPRINT_MISMATCH",
                result.preparation_fingerprint,
                expected_preparation_fingerprint,
            )

    @staticmethod
    def _validate_capability_profile(
        result: RuntimeAdapterPreparationResult,
    ) -> None:
        profile = result.capability_profile
        if profile != result.request.capability_profile:
            _raise_consistency(
                "ADAPTER_CAPABILITY_PROFILE_MISMATCH",
                "result_request_profile_difference",
                "identical_profile",
            )
        if (
            profile.profile_name != ADAPTER_PROFILE_NAME
            or profile.profile_version != ADAPTER_PROFILE_VERSION
            or not profile.supports_controlled_submission
            or any(
                getattr(profile, name)
                for name in ADAPTER_PROHIBITED_CAPABILITIES
            )
        ):
            _raise_consistency(
                "ADAPTER_CAPABILITY_PROFILE_MISMATCH",
                "noncanonical_capability_profile",
                "offline_adapter_profile",
            )
        relevant_scope = (
            profile.supports_full_package_scope
            if result.request.is_full_package_request
            else profile.supports_partial_scope
        )
        if not relevant_scope:
            _raise_consistency(
                "ADAPTER_CAPABILITY_PROFILE_MISMATCH",
                False,
                "compatible_scope_capability",
            )

    @staticmethod
    def _validate_request_content(request: object) -> None:
        if (
            PureWindowsPath(request.source.source_name).is_absolute()
            or PurePosixPath(request.source.source_name).is_absolute()
            or _safe_name(request.source.source_name) != request.source.source_name
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                "unsafe_source_name",
                "basename_only",
            )
        if (
            request.adapter_unit_count != len(request.units)
            or request.adapter_unit_count <= 0
            or request.approved_unit_indices
            != tuple(unit.execution_unit_index for unit in request.units)
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                "unit_count_or_scope",
                "canonical_request_scope",
            )
        approved_count = 0
        for expected_index, unit in enumerate(request.units):
            if (
                unit.adapter_unit_index != expected_index
                or unit.submission_index != expected_index
            ):
                _raise_consistency(
                    "ADAPTER_UNIT_FINGERPRINT_MISMATCH",
                    unit.adapter_unit_index,
                    expected_index,
                )
            if (
                unit.source_character_start < 0
                or unit.source_character_end < unit.source_character_start
                or unit.source_character_end - unit.source_character_start
                != len(unit.text)
            ):
                _raise_consistency(
                    "ADAPTER_UNIT_OFFSET_INVALID",
                    unit.source_character_start,
                    unit.source_character_end,
                )
            if (
                unit.character_count != len(unit.text)
                or unit.non_whitespace_character_count
                != sum(not character.isspace() for character in unit.text)
                or unit.source_chunk_fingerprint != _sha256_text(unit.text)
            ):
                _raise_consistency(
                    "ADAPTER_UNIT_TEXT_MISMATCH",
                    "noncanonical_text_metadata",
                    "canonical_text_metadata",
                )
            if (
                unit.status != "prepared_for_runtime_adapter"
                or unit.runtime_attempt_count != 0
                or unit.provider_request_count != 0
                or unit.translation_result_attached is not False
            ):
                _raise_consistency(
                    "ADAPTER_UNIT_STATE_INVALID",
                    f"{unit.status}:{unit.runtime_attempt_count}:"
                    f"{unit.provider_request_count}:{unit.translation_result_attached}",
                    "prepared_for_runtime_adapter:0:0:False",
                )
            if (
                unit.runtime_adapter_unit_fingerprint
                != _adapter_unit_fingerprint(unit)
            ):
                _raise_consistency(
                    "ADAPTER_UNIT_FINGERPRINT_MISMATCH",
                    unit.runtime_adapter_unit_fingerprint,
                    "canonical_adapter_unit_fingerprint",
                )
            approved_count += unit.character_count
        expected_ratio = (
            approved_count / request.original_character_count
            if request.original_character_count > 0
            else 0.0
        )
        if (
            request.approved_character_count != approved_count
            or request.original_character_count <= 0
            or request.approval_coverage_ratio != expected_ratio
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                "coverage_metadata",
                "canonical_coverage_metadata",
            )
        if (
            request.is_full_package_request
            and _sha256_text(request.reconstruct_approved_text())
            != request.source.source_content_fingerprint
        ):
            _raise_consistency(
                "ADAPTER_UNIT_TEXT_MISMATCH",
                "full_text_fingerprint",
                request.source.source_content_fingerprint,
            )
        if (
            request.provider_execution_authorized is not True
            or request.translation_execution_authorized is not True
            or request.runtime_submission_authorized is not True
            or request.automatic_retry_authorized
            or request.automatic_fallback_authorized
            or request.output_replacement_authorized
            or request.runtime_submission_executed
            or request.provider_requests_executed != 0
            or request.translation_executions_completed != 0
        ):
            _raise_consistency(
                "ADAPTER_PREPARATION_INVALID",
                "authorization_or_execution_state",
                "authorized_but_not_executed",
            )

    @staticmethod
    def _validate_adapter_findings(
        result: RuntimeAdapterPreparationResult,
    ) -> None:
        request = result.request
        expected = [
            "RUNTIME_ADAPTER_REQUEST_PREPARED",
            "RUNTIME_EXECUTION_NOT_PERFORMED",
            "PROVIDER_EXECUTION_NOT_PERFORMED",
            "TRANSLATION_EXECUTION_NOT_PERFORMED",
        ]
        if request.status == ADAPTER_WARNING_STATUS:
            expected.append("SUBMISSION_WARNING_PROPAGATED")
        expected.append(
            "FULL_PACKAGE_ADAPTER_REQUEST"
            if request.is_full_package_request
            else "PARTIAL_SCOPE_ADAPTER_REQUEST"
        )
        expected.extend(
            (
                "PROVIDER_CAPABILITY_NOT_AVAILABLE",
                "TRANSLATION_CAPABILITY_NOT_AVAILABLE",
                "AUTOMATIC_RETRY_NOT_SUPPORTED",
                "AUTOMATIC_FALLBACK_NOT_SUPPORTED",
                "OUTPUT_REPLACEMENT_NOT_SUPPORTED",
                "OUTPUT_WRITE_NOT_SUPPORTED",
                "RESUME_WRITE_NOT_SUPPORTED",
                "CACHE_WRITE_NOT_SUPPORTED",
                "PRODUCTION_HOOK_NOT_SUPPORTED",
            )
        )
        if (
            [finding.code for finding in request.findings] != expected
            or request.findings != result.findings
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                "noncanonical_findings",
                ",".join(expected),
            )
        if any(
            finding.severity != ADAPTER_FINDING_SEVERITIES.get(finding.code)
            or finding.message != ADAPTER_FINDING_MESSAGES.get(finding.code)
            for finding in request.findings
        ):
            _raise_consistency(
                "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
                "modified_finding_policy",
                "canonical_adapter_findings",
            )

    def _map_step(self, unit: object) -> ControlledRuntimeExecutionStep:
        payload = {
            "step_index": 0,
            "adapter_unit_index": unit.adapter_unit_index,
            "submission_index": unit.submission_index,
            "execution_unit_index": unit.execution_unit_index,
            "execution_unit_id": unit.execution_unit_id,
            "source_character_start": unit.source_character_start,
            "source_character_end": unit.source_character_end,
            "section_indices": list(unit.section_indices),
            "source_chunk_fingerprint": unit.source_chunk_fingerprint,
            "execution_unit_fingerprint": unit.execution_unit_fingerprint,
            "runtime_submission_unit_fingerprint": (
                unit.runtime_submission_unit_fingerprint
            ),
            "runtime_adapter_unit_fingerprint": (
                unit.runtime_adapter_unit_fingerprint
            ),
            "planned_provider_request_limit": (
                self._policy.maximum_provider_requests_per_unit
            ),
            "planned_retry_limit": 0,
            "planned_fallback_limit": 0,
            "status": STEP_STATUS,
            "runtime_attempt_count": 0,
            "provider_request_count": 0,
            "translation_result_attached": False,
        }
        return ControlledRuntimeExecutionStep(
            step_index=0,
            adapter_unit_index=unit.adapter_unit_index,
            submission_index=unit.submission_index,
            execution_unit_index=unit.execution_unit_index,
            execution_unit_id=unit.execution_unit_id,
            text=unit.text,
            source_character_start=unit.source_character_start,
            source_character_end=unit.source_character_end,
            section_indices=unit.section_indices,
            source_chunk_fingerprint=unit.source_chunk_fingerprint,
            execution_unit_fingerprint=unit.execution_unit_fingerprint,
            runtime_submission_unit_fingerprint=(
                unit.runtime_submission_unit_fingerprint
            ),
            runtime_adapter_unit_fingerprint=(
                unit.runtime_adapter_unit_fingerprint
            ),
            planned_provider_request_limit=(
                self._policy.maximum_provider_requests_per_unit
            ),
            planned_retry_limit=0,
            planned_fallback_limit=0,
            status=STEP_STATUS,
            runtime_attempt_count=0,
            provider_request_count=0,
            translation_result_attached=False,
            execution_step_fingerprint=_sha256_payload(payload),
        )

    @staticmethod
    def _success_findings(
        *,
        warning: bool,
    ) -> tuple[ControlledRuntimeExecutionFinding, ...]:
        findings = _FindingCollector()
        findings.add("CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED")
        findings.add("SINGLE_UNIT_EXECUTION_SCOPE")
        if warning:
            findings.add("ADAPTER_WARNING_PROPAGATED")
        findings.add("EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED")
        findings.add("RUNTIME_EXECUTION_NOT_STARTED")
        findings.add("RUNTIME_EXECUTION_NOT_COMPLETED")
        findings.add("PROVIDER_REQUEST_COUNT_ZERO")
        findings.add("TRANSLATION_EXECUTION_COUNT_ZERO")
        findings.add("RUNTIME_EXECUTION_CAPABILITY_DISABLED")
        findings.add("PROVIDER_EXECUTION_CAPABILITY_DISABLED")
        findings.add("TRANSLATION_EXECUTION_CAPABILITY_DISABLED")
        return findings.ordered()


def _finding(
    code: str,
    *,
    observed_value: str | int | float | bool | None = None,
    required_value: str | int | float | bool | None = None,
) -> ControlledRuntimeExecutionFinding:
    return ControlledRuntimeExecutionFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=FINDING_MESSAGES[code],
        observed_value=observed_value,
        required_value=required_value,
    )


def _raise_consistency(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: str | int | float | bool | None,
) -> None:
    finding = _finding(
        code,
        observed_value=observed_value,
        required_value=required_value,
    )
    raise ControlledRuntimeExecutionConsistencyError(
        finding.message,
        finding=finding,
    )


def _raise_scope(code: str) -> None:
    finding = _finding(code)
    raise ControlledRuntimeExecutionScopeError(
        finding.message,
        finding=finding,
    )


def _raise_policy(message: str) -> None:
    raise ControlledRuntimeExecutionPolicyError(message)


def _safe_name(value: str) -> str:
    return PurePosixPath(PureWindowsPath(value).name).name


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _adapter_unit_fingerprint(unit: object) -> str:
    return _sha256_payload(
        {
            "adapter_unit_index": unit.adapter_unit_index,
            "submission_index": unit.submission_index,
            "execution_unit_index": unit.execution_unit_index,
            "execution_unit_id": unit.execution_unit_id,
            "source_character_start": unit.source_character_start,
            "source_character_end": unit.source_character_end,
            "section_indices": list(unit.section_indices),
            "heading_text": unit.heading_text,
            "boundary_reason": unit.boundary_reason,
            "source_chunk_fingerprint": unit.source_chunk_fingerprint,
            "execution_unit_fingerprint": unit.execution_unit_fingerprint,
            "runtime_submission_unit_fingerprint": (
                unit.runtime_submission_unit_fingerprint
            ),
            "status": unit.status,
            "runtime_attempt_count": unit.runtime_attempt_count,
            "provider_request_count": unit.provider_request_count,
            "translation_result_attached": unit.translation_result_attached,
        }
    )


def _adapter_request_fingerprint(request: object) -> str:
    return _sha256_payload(
        {
            "schema_name": request.schema_name,
            "schema_version": request.schema_version,
            "strategy": request.strategy,
            "activation_gate": request.activation_gate,
            "source": asdict(request.source),
            "capability_profile": asdict(request.capability_profile),
            "approved_unit_indices": list(request.approved_unit_indices),
            "adapter_unit_fingerprints": [
                unit.runtime_adapter_unit_fingerprint for unit in request.units
            ],
            "adapter_unit_count": request.adapter_unit_count,
            "original_execution_unit_count": (
                request.original_execution_unit_count
            ),
            "approved_character_count": request.approved_character_count,
            "original_character_count": request.original_character_count,
            "approval_coverage_ratio": request.approval_coverage_ratio,
            "status": request.status,
            "action": request.action,
            "finding_codes": [finding.code for finding in request.findings],
            "authorization_flags": {
                "provider_execution_authorized": (
                    request.provider_execution_authorized
                ),
                "translation_execution_authorized": (
                    request.translation_execution_authorized
                ),
                "runtime_submission_authorized": (
                    request.runtime_submission_authorized
                ),
                "automatic_retry_authorized": (
                    request.automatic_retry_authorized
                ),
                "automatic_fallback_authorized": (
                    request.automatic_fallback_authorized
                ),
                "output_replacement_authorized": (
                    request.output_replacement_authorized
                ),
            },
            "runtime_submission_executed": request.runtime_submission_executed,
            "provider_requests_executed": request.provider_requests_executed,
            "translation_executions_completed": (
                request.translation_executions_completed
            ),
        }
    )


def _adapter_preparation_fingerprint(
    result: RuntimeAdapterPreparationResult,
) -> str:
    return _sha256_payload(
        {
            "runtime_adapter_request_fingerprint": (
                result.request.runtime_adapter_request_fingerprint
            ),
            "capability_profile": asdict(result.capability_profile),
            "prepared": result.prepared,
            "compatible": result.compatible,
            "runtime_invoked": result.runtime_invoked,
            "provider_invoked": result.provider_invoked,
            "translation_invoked": result.translation_invoked,
            "status": result.status,
            "action": result.action,
            "finding_codes": [finding.code for finding in result.findings],
        }
    )


def _plan_fingerprint(
    *,
    source: ControlledRuntimeExecutionSourceReference,
    policy: ControlledRuntimeExecutionPolicy,
    steps: tuple[ControlledRuntimeExecutionStep, ...],
    selected_indices: tuple[int, ...],
    available_count: int,
    planned_character_count: int,
    approved_character_count: int,
    planned_coverage: float,
    status: str,
    findings: tuple[ControlledRuntimeExecutionFinding, ...],
    request: object,
) -> str:
    return _sha256_payload(
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "strategy": STRATEGY,
            "activation_gate": ACTIVATION_GATE,
            "source": asdict(source),
            "policy": asdict(policy),
            "selected_adapter_unit_indices": list(selected_indices),
            "step_fingerprints": [
                step.execution_step_fingerprint for step in steps
            ],
            "planned_step_count": len(steps),
            "available_adapter_unit_count": available_count,
            "planned_character_count": planned_character_count,
            "approved_character_count": approved_character_count,
            "planned_approval_coverage_ratio": planned_coverage,
            "status": status,
            "action": HOLD_ACTION,
            "finding_codes": [finding.code for finding in findings],
            "authorization_flags": {
                "runtime_execution_authorized": (
                    request.runtime_submission_authorized
                ),
                "provider_execution_authorized": (
                    request.provider_execution_authorized
                ),
                "translation_execution_authorized": (
                    request.translation_execution_authorized
                ),
            },
            "enablement_flags": {
                "runtime_execution_enabled": policy.runtime_execution_enabled,
                "provider_execution_enabled": policy.provider_execution_enabled,
                "translation_execution_enabled": (
                    policy.translation_execution_enabled
                ),
            },
            "automatic_retry_authorized": request.automatic_retry_authorized,
            "automatic_fallback_authorized": (
                request.automatic_fallback_authorized
            ),
            "output_replacement_authorized": (
                request.output_replacement_authorized
            ),
            "execution_started": False,
            "execution_completed": False,
            "provider_requests_executed": 0,
            "translation_executions_completed": 0,
        }
    )
