from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import PurePosixPath, PureWindowsPath

from core.controlled_runtime_submission import RuntimeSubmissionPackage
from core.controlled_runtime_submission.policy import (
    ACTIVATION_GATE as SUBMISSION_ACTIVATION_GATE,
    FINDING_MESSAGES as SUBMISSION_FINDING_MESSAGES,
    FINDING_SEVERITIES as SUBMISSION_FINDING_SEVERITIES,
    HOLD_ACTION as SUBMISSION_HOLD_ACTION,
    PACKAGE_STATUS as SUBMISSION_STATUS,
    PACKAGE_WARNING_STATUS as SUBMISSION_WARNING_STATUS,
    SCHEMA_NAME as SUBMISSION_SCHEMA_NAME,
    SCHEMA_VERSION as SUBMISSION_SCHEMA_VERSION,
    STRATEGY as SUBMISSION_STRATEGY,
)

from .errors import (
    InvalidRuntimeAdapterInputError,
    RuntimeAdapterCapabilityError,
    RuntimeAdapterConsistencyError,
    RuntimeAdapterInvariantError,
)
from .models import (
    RuntimeAdapterCapabilityProfile,
    RuntimeAdapterFinding,
    RuntimeAdapterPreparationResult,
    RuntimeAdapterRequest,
    RuntimeAdapterSourceReference,
    RuntimeAdapterUnit,
)
from .policy import (
    ACTIVATION_GATE,
    DEFAULT_CAPABILITY_PROFILE,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    HOLD_ACTION,
    PACKAGE_STATUS,
    PACKAGE_WARNING_STATUS,
    PROFILE_NAME,
    PROFILE_VERSION,
    PROHIBITED_CAPABILITIES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STRATEGY,
    UNIT_STATUS,
)


class _FindingCollector:
    def __init__(self) -> None:
        self._items: dict[tuple[str, int | None], RuntimeAdapterFinding] = {}

    def add(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        self._items.setdefault(
            (code, unit_index),
            RuntimeAdapterFinding(
                code=code,
                severity=FINDING_SEVERITIES[code],
                message=FINDING_MESSAGES[code],
                unit_index=unit_index,
                observed_value=observed_value,
                required_value=required_value,
            ),
        )

    def ordered(self) -> tuple[RuntimeAdapterFinding, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda finding: (
                    FINDING_ORDER[finding.code],
                    -1 if finding.unit_index is None else finding.unit_index,
                ),
            )
        )


class ControlledRuntimeAdapter:
    """Map a canonical submission into an offline adapter request contract."""

    def __init__(
        self,
        capability_profile: RuntimeAdapterCapabilityProfile | None = None,
    ) -> None:
        profile = (
            DEFAULT_CAPABILITY_PROFILE
            if capability_profile is None
            else capability_profile
        )
        if not isinstance(profile, RuntimeAdapterCapabilityProfile):
            raise InvalidRuntimeAdapterInputError(
                "capability_profile must be a RuntimeAdapterCapabilityProfile"
            )
        self._validate_profile_boundary(profile)
        self._capability_profile = profile

    def prepare(
        self,
        *,
        submission_package: RuntimeSubmissionPackage,
    ) -> RuntimeAdapterPreparationResult:
        if not isinstance(submission_package, RuntimeSubmissionPackage):
            raise InvalidRuntimeAdapterInputError(
                "submission_package must be a RuntimeSubmissionPackage"
            )
        self._validate_submission(submission_package)
        is_full = submission_package.is_full_package_submission
        self._validate_profile_compatibility(is_full)

        units = tuple(
            self._map_unit(adapter_index, unit)
            for adapter_index, unit in enumerate(submission_package.units)
        )
        findings = self._success_findings(submission_package, is_full)
        status = (
            PACKAGE_WARNING_STATUS
            if submission_package.status == SUBMISSION_WARNING_STATUS
            else PACKAGE_STATUS
        )
        source = RuntimeAdapterSourceReference(
            source_name=_safe_name(submission_package.source.source_name),
            source_content_fingerprint=(
                submission_package.source.source_content_fingerprint
            ),
            execution_package_fingerprint=(
                submission_package.source.execution_package_fingerprint
            ),
            authorization_fingerprint=(
                submission_package.source.authorization_fingerprint
            ),
            approval_record_fingerprint=(
                submission_package.source.approval_record_fingerprint
            ),
            runtime_submission_package_fingerprint=(
                submission_package.runtime_submission_package_fingerprint
            ),
            manifest_fingerprint=submission_package.source.manifest_fingerprint,
            segmentation_fingerprint=(
                submission_package.source.segmentation_fingerprint
            ),
            chunk_plan_fingerprint=(
                submission_package.source.chunk_plan_fingerprint
            ),
            preparation_fingerprint=(
                submission_package.source.preparation_fingerprint
            ),
        )
        request_fingerprint = _request_fingerprint(
            source=source,
            profile=self._capability_profile,
            units=units,
            approved_unit_indices=submission_package.approved_unit_indices,
            original_execution_unit_count=(
                submission_package.original_execution_unit_count
            ),
            approved_character_count=submission_package.approved_character_count,
            original_character_count=submission_package.original_character_count,
            approval_coverage_ratio=submission_package.approval_coverage_ratio,
            status=status,
            action=HOLD_ACTION,
            findings=findings,
            submission=submission_package,
        )
        request = RuntimeAdapterRequest(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            strategy=STRATEGY,
            activation_gate=ACTIVATION_GATE,
            source=source,
            capability_profile=self._capability_profile,
            units=units,
            approved_unit_indices=submission_package.approved_unit_indices,
            adapter_unit_count=len(units),
            original_execution_unit_count=(
                submission_package.original_execution_unit_count
            ),
            approved_character_count=submission_package.approved_character_count,
            original_character_count=submission_package.original_character_count,
            approval_coverage_ratio=submission_package.approval_coverage_ratio,
            status=status,
            action=HOLD_ACTION,
            findings=findings,
            summary=(
                f"Offline runtime adapter request prepared for {len(units)} unit(s); "
                "runtime, provider, and translation were not invoked."
            ),
            provider_execution_authorized=(
                submission_package.provider_execution_authorized
            ),
            translation_execution_authorized=(
                submission_package.translation_execution_authorized
            ),
            runtime_submission_authorized=(
                submission_package.runtime_submission_authorized
            ),
            automatic_retry_authorized=(
                submission_package.automatic_retry_authorized
            ),
            automatic_fallback_authorized=(
                submission_package.automatic_fallback_authorized
            ),
            output_replacement_authorized=(
                submission_package.output_replacement_authorized
            ),
            runtime_submission_executed=(
                submission_package.runtime_submission_executed
            ),
            provider_requests_executed=(
                submission_package.provider_requests_executed
            ),
            translation_executions_completed=(
                submission_package.translation_executions_completed
            ),
            runtime_adapter_request_fingerprint=request_fingerprint,
        )
        if (
            request.reconstruct_approved_text()
            != submission_package.reconstruct_approved_text()
        ):
            raise RuntimeAdapterInvariantError(
                "Adapter request does not reconstruct the approved submission text."
            )
        preparation_fingerprint = _preparation_fingerprint(
            request=request,
            profile=self._capability_profile,
            findings=findings,
            status=status,
            action=HOLD_ACTION,
        )
        return RuntimeAdapterPreparationResult(
            request=request,
            capability_profile=self._capability_profile,
            prepared=True,
            compatible=True,
            runtime_invoked=False,
            provider_invoked=False,
            translation_invoked=False,
            status=status,
            action=HOLD_ACTION,
            findings=findings,
            summary=(
                "Controlled runtime adapter preparation completed offline; "
                "no execution capability was invoked."
            ),
            preparation_fingerprint=preparation_fingerprint,
        )

    @staticmethod
    def _validate_profile_boundary(
        profile: RuntimeAdapterCapabilityProfile,
    ) -> None:
        if (
            profile.profile_name != PROFILE_NAME
            or profile.profile_version != PROFILE_VERSION
        ):
            _raise_capability(
                "CAPABILITY_PROFILE_MISMATCH",
                f"{profile.profile_name}:{profile.profile_version}",
                f"{PROFILE_NAME}:{PROFILE_VERSION}",
            )
        boolean_fields = (
            "supports_controlled_submission",
            "supports_partial_scope",
            "supports_full_package_scope",
            *PROHIBITED_CAPABILITIES,
        )
        if any(type(getattr(profile, name)) is not bool for name in boolean_fields):
            _raise_capability(
                "CAPABILITY_PROFILE_MISMATCH",
                "non_boolean_capability",
                "boolean_capability",
            )
        enabled = tuple(
            name for name in PROHIBITED_CAPABILITIES if getattr(profile, name)
        )
        if enabled:
            _raise_capability(
                "CAPABILITY_PROFILE_MISMATCH",
                ",".join(enabled),
                "offline_only",
            )

    def _validate_profile_compatibility(self, is_full: bool) -> None:
        if not self._capability_profile.supports_controlled_submission:
            _raise_capability(
                "CAPABILITY_PROFILE_MISMATCH",
                False,
                "supports_controlled_submission",
            )
        scope_capability = (
            self._capability_profile.supports_full_package_scope
            if is_full
            else self._capability_profile.supports_partial_scope
        )
        if not scope_capability:
            _raise_capability(
                "CAPABILITY_PROFILE_MISMATCH",
                False,
                "compatible_scope_capability",
            )

    def _validate_submission(self, submission: RuntimeSubmissionPackage) -> None:
        contract = (
            ("schema_name", SUBMISSION_SCHEMA_NAME, "SUBMISSION_SCHEMA_MISMATCH"),
            ("schema_version", SUBMISSION_SCHEMA_VERSION, "SUBMISSION_VERSION_MISMATCH"),
            ("strategy", SUBMISSION_STRATEGY, "SUBMISSION_STRATEGY_MISMATCH"),
            (
                "activation_gate",
                SUBMISSION_ACTIVATION_GATE,
                "SUBMISSION_GATE_MISMATCH",
            ),
        )
        for name, required, code in contract:
            if getattr(submission, name) != required:
                _raise_consistency(code, getattr(submission, name), required)
        if submission.status not in {
            SUBMISSION_STATUS,
            SUBMISSION_WARNING_STATUS,
        } or submission.action != SUBMISSION_HOLD_ACTION:
            _raise_consistency(
                "SUBMISSION_GATE_MISMATCH",
                f"{submission.status}:{submission.action}",
                "prepared_submission:hold_for_runtime_adapter",
            )
        if (
            PureWindowsPath(submission.source.source_name).is_absolute()
            or PurePosixPath(submission.source.source_name).is_absolute()
            or _safe_name(submission.source.source_name)
            != submission.source.source_name
        ):
            _raise_consistency(
                "SUBMISSION_FINGERPRINT_MISMATCH",
                "unsafe_source_name",
                "basename_only",
            )
        if submission.submission_unit_count != len(submission.units):
            _raise_consistency(
                "SUBMISSION_UNIT_COUNT_MISMATCH",
                submission.submission_unit_count,
                len(submission.units),
            )
        if not submission.units or not submission.approved_unit_indices:
            _raise_consistency(
                "SUBMISSION_SCOPE_MISMATCH",
                len(submission.units),
                "non_empty_scope",
            )
        if (
            len(set(submission.approved_unit_indices))
            != len(submission.approved_unit_indices)
            or submission.approved_unit_indices
            != tuple(sorted(submission.approved_unit_indices))
            or any(
                isinstance(index, bool) or not isinstance(index, int) or index < 0
                for index in submission.approved_unit_indices
            )
        ):
            _raise_consistency(
                "SUBMISSION_SCOPE_MISMATCH",
                "invalid_indices",
                "unique_ascending_nonnegative_indices",
            )
        if submission.approved_unit_indices != tuple(
            unit.execution_unit_index for unit in submission.units
        ):
            _raise_consistency(
                "SUBMISSION_UNIT_ORDER_MISMATCH",
                "unit_scope_order",
                "approved_unit_indices",
            )
        approved_character_count = 0
        for expected_index, unit in enumerate(submission.units):
            if unit.submission_index != expected_index:
                _raise_consistency(
                    "SUBMISSION_UNIT_ORDER_MISMATCH",
                    unit.submission_index,
                    expected_index,
                    unit_index=unit.execution_unit_index,
                )
            if (
                unit.source_character_start < 0
                or unit.source_character_end < unit.source_character_start
                or unit.source_character_end - unit.source_character_start
                != len(unit.text)
            ):
                _raise_consistency(
                    "SUBMISSION_UNIT_OFFSET_INVALID",
                    unit.source_character_start,
                    unit.source_character_end,
                    unit_index=unit.execution_unit_index,
                )
            if (
                not isinstance(unit.section_indices, tuple)
                or unit.character_count != len(unit.text)
                or unit.non_whitespace_character_count
                != sum(not character.isspace() for character in unit.text)
                or unit.source_chunk_fingerprint != _sha256_text(unit.text)
            ):
                _raise_consistency(
                    "SUBMISSION_UNIT_TEXT_MISMATCH",
                    "noncanonical_unit_content",
                    "canonical_unit_content",
                    unit_index=unit.execution_unit_index,
                )
            if (
                unit.status != "queued_for_controlled_submission"
                or unit.runtime_attempt_count != 0
                or unit.provider_request_count != 0
                or unit.translation_result_attached is not False
            ):
                code = (
                    "PROVIDER_REQUEST_ALREADY_DETECTED"
                    if unit.provider_request_count
                    else "TRANSLATION_RESULT_ALREADY_DETECTED"
                    if unit.translation_result_attached
                    else "SUBMISSION_ALREADY_EXECUTED"
                )
                _raise_consistency(
                    code,
                    f"{unit.status}:{unit.runtime_attempt_count}:"
                    f"{unit.provider_request_count}:{unit.translation_result_attached}",
                    "queued_for_controlled_submission:0:0:False",
                    unit_index=unit.execution_unit_index,
                )
            if (
                unit.runtime_submission_unit_fingerprint
                != _submission_unit_fingerprint(unit)
            ):
                _raise_consistency(
                    "SUBMISSION_UNIT_FINGERPRINT_MISMATCH",
                    unit.runtime_submission_unit_fingerprint,
                    "canonical_submission_unit_fingerprint",
                    unit_index=unit.execution_unit_index,
                )
            approved_character_count += unit.character_count
        expected_ratio = (
            approved_character_count / submission.original_character_count
            if submission.original_character_count > 0
            else 0.0
        )
        if (
            submission.original_execution_unit_count <= 0
            or any(
                index >= submission.original_execution_unit_count
                for index in submission.approved_unit_indices
            )
            or submission.character_count != approved_character_count
            or submission.covered_character_count != approved_character_count
            or submission.coverage_ratio != 1.0
            or submission.approved_character_count != approved_character_count
            or submission.original_character_count <= 0
            or submission.approval_coverage_ratio != expected_ratio
        ):
            _raise_consistency(
                "SUBMISSION_SCOPE_MISMATCH",
                "coverage_or_scope_metadata",
                "canonical_approval_coverage",
            )
        reconstructed = submission.reconstruct_approved_text()
        if (
            submission.is_full_package_submission
            and _sha256_text(reconstructed)
            != submission.source.source_content_fingerprint
        ):
            _raise_consistency(
                "SUBMISSION_UNIT_TEXT_MISMATCH",
                "full_reconstruction_fingerprint",
                submission.source.source_content_fingerprint,
            )
        controlled_flags = (
            submission.provider_execution_authorized,
            submission.translation_execution_authorized,
            submission.runtime_submission_authorized,
        )
        if controlled_flags != (True, True, True):
            _raise_consistency(
                "SUBMISSION_SCOPE_MISMATCH",
                str(controlled_flags),
                "True:True:True",
            )
        if (
            submission.automatic_retry_authorized
            or submission.automatic_fallback_authorized
            or submission.output_replacement_authorized
        ):
            _raise_consistency(
                "SUBMISSION_ALREADY_EXECUTED",
                "prohibited_authorization_enabled",
                False,
            )
        if submission.runtime_submission_executed:
            _raise_consistency("SUBMISSION_ALREADY_EXECUTED", True, False)
        if submission.provider_requests_executed != 0:
            _raise_consistency(
                "PROVIDER_REQUEST_ALREADY_DETECTED",
                submission.provider_requests_executed,
                0,
            )
        if submission.translation_executions_completed != 0:
            _raise_consistency(
                "TRANSLATION_RESULT_ALREADY_DETECTED",
                submission.translation_executions_completed,
                0,
            )
        self._validate_submission_findings(submission)
        expected_fingerprint = _submission_package_fingerprint(submission)
        if submission.runtime_submission_package_fingerprint != expected_fingerprint:
            _raise_consistency(
                "SUBMISSION_FINGERPRINT_MISMATCH",
                submission.runtime_submission_package_fingerprint,
                expected_fingerprint,
            )

    @staticmethod
    def _validate_submission_findings(
        submission: RuntimeSubmissionPackage,
    ) -> None:
        codes = ["CONTROLLED_RUNTIME_SUBMISSION_PREPARED"]
        codes.append(
            "FULL_PACKAGE_SUBMISSION"
            if submission.is_full_package_submission
            else "PARTIAL_SCOPE_SUBMISSION"
        )
        if submission.status == SUBMISSION_WARNING_STATUS:
            codes.append("PACKAGE_WARNING_PROPAGATED")
        codes.extend(
            (
                "RUNTIME_SUBMISSION_NOT_EXECUTED",
                "PROVIDER_REQUEST_COUNT_ZERO",
                "TRANSLATION_EXECUTION_COUNT_ZERO",
            )
        )
        if [finding.code for finding in submission.findings] != codes:
            _raise_consistency(
                "SUBMISSION_FINGERPRINT_MISMATCH",
                "noncanonical_finding_codes",
                ",".join(codes),
            )
        if any(
            finding.severity != SUBMISSION_FINDING_SEVERITIES.get(finding.code)
            or finding.message != SUBMISSION_FINDING_MESSAGES.get(finding.code)
            for finding in submission.findings
        ):
            _raise_consistency(
                "SUBMISSION_FINGERPRINT_MISMATCH",
                "modified_finding_policy",
                "canonical_finding_policy",
            )

    @staticmethod
    def _map_unit(adapter_index: int, unit: object) -> RuntimeAdapterUnit:
        payload = {
            "adapter_unit_index": adapter_index,
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
            "status": UNIT_STATUS,
            "runtime_attempt_count": 0,
            "provider_request_count": 0,
            "translation_result_attached": False,
        }
        return RuntimeAdapterUnit(
            adapter_unit_index=adapter_index,
            submission_index=unit.submission_index,
            execution_unit_index=unit.execution_unit_index,
            execution_unit_id=unit.execution_unit_id,
            text=unit.text,
            source_character_start=unit.source_character_start,
            source_character_end=unit.source_character_end,
            section_indices=unit.section_indices,
            heading_text=unit.heading_text,
            boundary_reason=unit.boundary_reason,
            character_count=unit.character_count,
            non_whitespace_character_count=unit.non_whitespace_character_count,
            source_chunk_fingerprint=unit.source_chunk_fingerprint,
            execution_unit_fingerprint=unit.execution_unit_fingerprint,
            runtime_submission_unit_fingerprint=(
                unit.runtime_submission_unit_fingerprint
            ),
            runtime_adapter_unit_fingerprint=_sha256_payload(payload),
            status=UNIT_STATUS,
            runtime_attempt_count=0,
            provider_request_count=0,
            translation_result_attached=False,
        )

    @staticmethod
    def _success_findings(
        submission: RuntimeSubmissionPackage,
        is_full: bool,
    ) -> tuple[RuntimeAdapterFinding, ...]:
        findings = _FindingCollector()
        findings.add("RUNTIME_ADAPTER_REQUEST_PREPARED")
        findings.add("RUNTIME_EXECUTION_NOT_PERFORMED")
        findings.add("PROVIDER_EXECUTION_NOT_PERFORMED")
        findings.add("TRANSLATION_EXECUTION_NOT_PERFORMED")
        if submission.status == SUBMISSION_WARNING_STATUS:
            findings.add("SUBMISSION_WARNING_PROPAGATED")
        findings.add(
            "FULL_PACKAGE_ADAPTER_REQUEST"
            if is_full
            else "PARTIAL_SCOPE_ADAPTER_REQUEST"
        )
        for code in (
            "PROVIDER_CAPABILITY_NOT_AVAILABLE",
            "TRANSLATION_CAPABILITY_NOT_AVAILABLE",
            "AUTOMATIC_RETRY_NOT_SUPPORTED",
            "AUTOMATIC_FALLBACK_NOT_SUPPORTED",
            "OUTPUT_REPLACEMENT_NOT_SUPPORTED",
            "OUTPUT_WRITE_NOT_SUPPORTED",
            "RESUME_WRITE_NOT_SUPPORTED",
            "CACHE_WRITE_NOT_SUPPORTED",
            "PRODUCTION_HOOK_NOT_SUPPORTED",
        ):
            findings.add(code)
        return findings.ordered()


def _raise_consistency(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: str | int | float | bool | None,
    *,
    unit_index: int | None = None,
) -> None:
    finding = RuntimeAdapterFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=FINDING_MESSAGES[code],
        unit_index=unit_index,
        observed_value=observed_value,
        required_value=required_value,
    )
    raise RuntimeAdapterConsistencyError(finding.message, finding=finding)


def _raise_capability(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: str | int | float | bool | None,
) -> None:
    finding = RuntimeAdapterFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=FINDING_MESSAGES[code],
        observed_value=observed_value,
        required_value=required_value,
    )
    raise RuntimeAdapterCapabilityError(finding.message, finding=finding)


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


def _submission_unit_fingerprint(unit: object) -> str:
    return _sha256_payload(
        {
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
            "status": unit.status,
            "runtime_attempt_count": unit.runtime_attempt_count,
            "provider_request_count": unit.provider_request_count,
            "translation_result_attached": unit.translation_result_attached,
        }
    )


def _submission_package_fingerprint(
    submission: RuntimeSubmissionPackage,
) -> str:
    return _sha256_payload(
        {
            "schema_name": submission.schema_name,
            "schema_version": submission.schema_version,
            "strategy": submission.strategy,
            "activation_gate": submission.activation_gate,
            "source": asdict(submission.source),
            "approved_unit_indices": list(submission.approved_unit_indices),
            "submission_unit_fingerprints": [
                unit.runtime_submission_unit_fingerprint
                for unit in submission.units
            ],
            "submission_unit_count": submission.submission_unit_count,
            "original_execution_unit_count": (
                submission.original_execution_unit_count
            ),
            "approved_character_count": submission.approved_character_count,
            "original_character_count": submission.original_character_count,
            "approval_coverage_ratio": submission.approval_coverage_ratio,
            "status": submission.status,
            "action": submission.action,
            "finding_codes": [
                finding.code for finding in submission.findings
            ],
            "authorization_flags": {
                "provider_execution_authorized": (
                    submission.provider_execution_authorized
                ),
                "translation_execution_authorized": (
                    submission.translation_execution_authorized
                ),
                "runtime_submission_authorized": (
                    submission.runtime_submission_authorized
                ),
                "automatic_retry_authorized": (
                    submission.automatic_retry_authorized
                ),
                "automatic_fallback_authorized": (
                    submission.automatic_fallback_authorized
                ),
                "output_replacement_authorized": (
                    submission.output_replacement_authorized
                ),
            },
            "runtime_submission_executed": (
                submission.runtime_submission_executed
            ),
            "provider_requests_executed": (
                submission.provider_requests_executed
            ),
            "translation_executions_completed": (
                submission.translation_executions_completed
            ),
        }
    )


def _request_fingerprint(
    *,
    source: RuntimeAdapterSourceReference,
    profile: RuntimeAdapterCapabilityProfile,
    units: tuple[RuntimeAdapterUnit, ...],
    approved_unit_indices: tuple[int, ...],
    original_execution_unit_count: int,
    approved_character_count: int,
    original_character_count: int,
    approval_coverage_ratio: float,
    status: str,
    action: str,
    findings: tuple[RuntimeAdapterFinding, ...],
    submission: RuntimeSubmissionPackage,
) -> str:
    return _sha256_payload(
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "strategy": STRATEGY,
            "activation_gate": ACTIVATION_GATE,
            "source": asdict(source),
            "capability_profile": asdict(profile),
            "approved_unit_indices": list(approved_unit_indices),
            "adapter_unit_fingerprints": [
                unit.runtime_adapter_unit_fingerprint for unit in units
            ],
            "adapter_unit_count": len(units),
            "original_execution_unit_count": original_execution_unit_count,
            "approved_character_count": approved_character_count,
            "original_character_count": original_character_count,
            "approval_coverage_ratio": approval_coverage_ratio,
            "status": status,
            "action": action,
            "finding_codes": [finding.code for finding in findings],
            "authorization_flags": {
                "provider_execution_authorized": (
                    submission.provider_execution_authorized
                ),
                "translation_execution_authorized": (
                    submission.translation_execution_authorized
                ),
                "runtime_submission_authorized": (
                    submission.runtime_submission_authorized
                ),
                "automatic_retry_authorized": (
                    submission.automatic_retry_authorized
                ),
                "automatic_fallback_authorized": (
                    submission.automatic_fallback_authorized
                ),
                "output_replacement_authorized": (
                    submission.output_replacement_authorized
                ),
            },
            "runtime_submission_executed": (
                submission.runtime_submission_executed
            ),
            "provider_requests_executed": (
                submission.provider_requests_executed
            ),
            "translation_executions_completed": (
                submission.translation_executions_completed
            ),
        }
    )


def _preparation_fingerprint(
    *,
    request: RuntimeAdapterRequest,
    profile: RuntimeAdapterCapabilityProfile,
    findings: tuple[RuntimeAdapterFinding, ...],
    status: str,
    action: str,
) -> str:
    return _sha256_payload(
        {
            "runtime_adapter_request_fingerprint": (
                request.runtime_adapter_request_fingerprint
            ),
            "capability_profile": asdict(profile),
            "prepared": True,
            "compatible": True,
            "runtime_invoked": False,
            "provider_invoked": False,
            "translation_invoked": False,
            "status": status,
            "action": action,
            "finding_codes": [finding.code for finding in findings],
        }
    )
