from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import PurePosixPath, PureWindowsPath

from core.book_intake import get_book_intake_freeze_metadata
from core.book_preparation import get_book_preparation_freeze_metadata
from core.translation_execution_approval import (
    ExecutionApprovalRecord,
    get_translation_execution_governance_freeze_metadata,
)
from core.translation_execution_approval.policy import (
    ACTIVATION_GATE as APPROVAL_ACTIVATION_GATE,
    APPROVED_ACTION,
    APPROVED_DECISION,
    FINDING_MESSAGES as APPROVAL_FINDING_MESSAGES,
    FINDING_SEVERITIES as APPROVAL_FINDING_SEVERITIES,
    SCHEMA_NAME as APPROVAL_SCHEMA_NAME,
    SCHEMA_VERSION as APPROVAL_SCHEMA_VERSION,
    STRATEGY as APPROVAL_STRATEGY,
)
from core.translation_execution_authorization import (
    ExecutionAuthorizationDecision,
    TranslationExecutionAuthorizationError,
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_package import TranslationExecutionPackage

from .errors import (
    InvalidRuntimeSubmissionInputError,
    RuntimeSubmissionConsistencyError,
    RuntimeSubmissionInvariantError,
    RuntimeSubmissionPolicyError,
    RuntimeSubmissionScopeError,
)
from .models import (
    RuntimeSubmissionFinding,
    RuntimeSubmissionPackage,
    RuntimeSubmissionSourceReference,
    RuntimeSubmissionUnit,
)
from .policy import (
    DEFAULT_POLICY,
    PACKAGE_STATUS,
    PACKAGE_WARNING_STATUS,
    ControlledRuntimeSubmissionPolicy,
)


class _FindingCollector:
    def __init__(self, policy: ControlledRuntimeSubmissionPolicy) -> None:
        self._policy = policy
        self._items: dict[tuple[str, int | None], RuntimeSubmissionFinding] = {}

    def add(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        key = (code, unit_index)
        self._items.setdefault(
            key,
            RuntimeSubmissionFinding(
                code=code,
                severity=self._policy.finding_severities[code],
                message=self._policy.finding_messages[code],
                unit_index=unit_index,
                observed_value=observed_value,
                required_value=required_value,
            ),
        )

    def ordered(self) -> tuple[RuntimeSubmissionFinding, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda finding: (
                    self._policy.finding_order[finding.code],
                    -1 if finding.unit_index is None else finding.unit_index,
                ),
            )
        )


class ControlledRuntimeSubmissionBuilder:
    """Prepare an immutable approved scope without executing runtime work."""

    def __init__(
        self, policy: ControlledRuntimeSubmissionPolicy = DEFAULT_POLICY
    ) -> None:
        if not isinstance(policy, ControlledRuntimeSubmissionPolicy):
            raise InvalidRuntimeSubmissionInputError(
                "policy must be a ControlledRuntimeSubmissionPolicy"
            )
        if policy != DEFAULT_POLICY:
            raise RuntimeSubmissionPolicyError(
                "The controlled runtime submission policy cannot be relaxed."
            )
        self._policy = policy

    def build(
        self,
        *,
        package: TranslationExecutionPackage,
        authorization_decision: ExecutionAuthorizationDecision,
        approval_record: ExecutionApprovalRecord,
    ) -> RuntimeSubmissionPackage:
        self._validate_input_types(package, authorization_decision, approval_record)
        self._validate_activation_gates(package, approval_record)
        self._validate_package_and_decision(package, authorization_decision)
        self._validate_approval_record(package, authorization_decision, approval_record)
        self._validate_scope(package, approval_record)

        units = tuple(
            self._map_unit(submission_index, package.units[execution_index])
            for submission_index, execution_index in enumerate(
                approval_record.approved_unit_indices
            )
        )
        approved_character_count = sum(unit.character_count for unit in units)
        original_character_count = package.character_count
        approval_coverage_ratio = (
            approved_character_count / original_character_count
            if original_character_count > 0
            else 0.0
        )
        is_full = approval_record.approved_unit_indices == tuple(
            range(package.unit_count)
        )

        findings = _FindingCollector(self._policy)
        findings.add("CONTROLLED_RUNTIME_SUBMISSION_PREPARED")
        findings.add("FULL_PACKAGE_SUBMISSION" if is_full else "PARTIAL_SCOPE_SUBMISSION")
        if package.status == "prepared_with_warnings":
            warning_codes = ",".join(
                dict.fromkeys(
                    finding.code
                    for finding in package.findings
                    if finding.severity == "warning"
                )
            )
            findings.add(
                "PACKAGE_WARNING_PROPAGATED",
                observed_value=warning_codes or "prepared_with_warnings",
            )
        findings.add("RUNTIME_SUBMISSION_NOT_EXECUTED")
        findings.add("PROVIDER_REQUEST_COUNT_ZERO")
        findings.add("TRANSLATION_EXECUTION_COUNT_ZERO")
        ordered_findings = findings.ordered()

        status = (
            PACKAGE_WARNING_STATUS
            if package.status == "prepared_with_warnings"
            else PACKAGE_STATUS
        )
        action = self._policy.status_actions[status]
        source = RuntimeSubmissionSourceReference(
            source_name=_safe_name(package.source.source_name),
            source_content_fingerprint=package.source.source_content_fingerprint,
            execution_package_fingerprint=package.execution_package_fingerprint,
            authorization_fingerprint=authorization_decision.authorization_fingerprint,
            approval_record_fingerprint=approval_record.approval_record_fingerprint,
            manifest_fingerprint=package.source.manifest_fingerprint,
            segmentation_fingerprint=package.source.segmentation_fingerprint,
            chunk_plan_fingerprint=package.source.chunk_plan_fingerprint,
            preparation_fingerprint=package.source.preparation_fingerprint,
        )
        package_fingerprint = self._package_fingerprint(
            source=source,
            units=units,
            approved_unit_indices=approval_record.approved_unit_indices,
            original_execution_unit_count=package.unit_count,
            approved_character_count=approved_character_count,
            original_character_count=original_character_count,
            approval_coverage_ratio=approval_coverage_ratio,
            status=status,
            action=action,
            findings=ordered_findings,
        )
        submission = RuntimeSubmissionPackage(
            schema_name=self._policy.schema_name,
            schema_version=self._policy.schema_version,
            strategy=self._policy.strategy,
            activation_gate=self._policy.activation_gate,
            source=source,
            units=units,
            approved_unit_indices=approval_record.approved_unit_indices,
            submission_unit_count=len(units),
            original_execution_unit_count=package.unit_count,
            character_count=approved_character_count,
            covered_character_count=approved_character_count,
            coverage_ratio=1.0,
            approved_character_count=approved_character_count,
            original_character_count=original_character_count,
            approval_coverage_ratio=approval_coverage_ratio,
            status=status,
            action=action,
            findings=ordered_findings,
            summary=(
                f"Controlled runtime submission prepared for {len(units)} approved "
                "unit(s); no runtime or provider execution was performed."
            ),
            **self._policy.controlled_authorization_flags,
            **self._policy.prohibited_authorization_flags,
            **self._policy.execution_state,
            runtime_submission_package_fingerprint=package_fingerprint,
        )
        if submission.reconstruct_approved_text() != "".join(
            package.units[index].text
            for index in approval_record.approved_unit_indices
        ):
            raise RuntimeSubmissionInvariantError(
                "Materialized submission does not reconstruct the approved text."
            )
        return submission

    @staticmethod
    def _validate_input_types(
        package: object, decision: object, record: object
    ) -> None:
        if not isinstance(package, TranslationExecutionPackage):
            raise InvalidRuntimeSubmissionInputError(
                "package must be a TranslationExecutionPackage"
            )
        if not isinstance(decision, ExecutionAuthorizationDecision):
            raise InvalidRuntimeSubmissionInputError(
                "authorization_decision must be an ExecutionAuthorizationDecision"
            )
        if not isinstance(record, ExecutionApprovalRecord):
            raise InvalidRuntimeSubmissionInputError(
                "approval_record must be an ExecutionApprovalRecord"
            )

    def _validate_activation_gates(
        self,
        package: TranslationExecutionPackage,
        record: ExecutionApprovalRecord,
    ) -> None:
        observed = (
            get_book_intake_freeze_metadata().activation_gate,
            get_book_preparation_freeze_metadata().activation_gate,
            get_translation_execution_governance_freeze_metadata().activation_gate,
            record.activation_gate,
        )
        if observed != self._policy.required_activation_gates:
            self._raise_consistency(
                "APPROVAL_RECORD_NOT_APPROVED",
                observed_value=",".join(observed),
                required_value=",".join(self._policy.required_activation_gates),
            )
        if package.activation_gate != "translation_execution_package_prepared":
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                observed_value=package.activation_gate,
                required_value="translation_execution_package_prepared",
            )

    def _validate_package_and_decision(
        self,
        package: TranslationExecutionPackage,
        decision: ExecutionAuthorizationDecision,
    ) -> None:
        if package.status not in {"prepared", "prepared_with_warnings"}:
            self._raise_consistency(
                "EXECUTION_UNIT_ALREADY_EXECUTED",
                observed_value=package.status,
                required_value="prepared",
            )
        for unit in package.units:
            if (
                unit.status != "prepared"
                or unit.attempt_count != 0
                or unit.provider_request_count != 0
                or unit.translation_result_attached is not False
            ):
                self._raise_consistency(
                    "EXECUTION_UNIT_ALREADY_EXECUTED",
                    unit_index=unit.index,
                    observed_value=(
                        f"{unit.status}:{unit.attempt_count}:"
                        f"{unit.provider_request_count}:"
                        f"{unit.translation_result_attached}"
                    ),
                    required_value="prepared:0:0:False",
                )
            if (
                unit.source_character_start < 0
                or unit.source_character_end < unit.source_character_start
                or unit.source_character_end - unit.source_character_start
                != len(unit.text)
            ):
                self._raise_consistency(
                    "EXECUTION_UNIT_OFFSET_INVALID", unit_index=unit.index
                )
            if (
                unit.character_count != len(unit.text)
                or unit.non_whitespace_character_count
                != sum(not character.isspace() for character in unit.text)
                or unit.source_chunk_fingerprint != _sha256_text(unit.text)
            ):
                self._raise_consistency(
                    "EXECUTION_UNIT_TEXT_MISMATCH", unit_index=unit.index
                )
            if unit.execution_unit_fingerprint != _execution_unit_fingerprint(unit):
                self._raise_consistency(
                    "EXECUTION_UNIT_FINGERPRINT_MISMATCH", unit_index=unit.index
                )
        if any(
            getattr(package, name) is not False
            for name in (
                *self._policy.controlled_authorization_flags,
                *self._policy.prohibited_authorization_flags,
            )
        ):
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                observed_value="package_authorization_flag_enabled",
                required_value=False,
            )
        try:
            expected_decision = TranslationExecutionAuthorizationEvaluator().evaluate(
                package
            )
        except TranslationExecutionAuthorizationError as error:
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                observed_value=getattr(
                    getattr(error, "finding", None), "code", "noncanonical_package"
                ),
                required_value="canonical_execution_package",
            )
        if (
            decision.package_fingerprint != package.execution_package_fingerprint
            or decision.package_fingerprint != expected_decision.package_fingerprint
        ):
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                observed_value=decision.package_fingerprint,
                required_value=package.execution_package_fingerprint,
            )
        if (
            decision.authorized is not False
            or decision.decision != "denied"
            or decision.requires_human_approval is not True
            or any(
                getattr(decision, name) is not False
                for name in (
                    *self._policy.controlled_authorization_flags,
                    *self._policy.prohibited_authorization_flags,
                )
            )
        ):
            self._raise_consistency(
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
                observed_value="noncanonical_authorization_state",
                required_value="default_denied",
            )
        if decision != expected_decision:
            self._raise_consistency(
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
                observed_value=decision.authorization_fingerprint,
                required_value=expected_decision.authorization_fingerprint,
            )

    def _validate_approval_record(
        self,
        package: TranslationExecutionPackage,
        decision: ExecutionAuthorizationDecision,
        record: ExecutionApprovalRecord,
    ) -> None:
        if record.package_fingerprint != package.execution_package_fingerprint:
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                observed_value=record.package_fingerprint,
                required_value=package.execution_package_fingerprint,
            )
        if record.authorization_fingerprint != decision.authorization_fingerprint:
            self._raise_consistency(
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
                observed_value=record.authorization_fingerprint,
                required_value=decision.authorization_fingerprint,
            )
        if (
            record.schema_name != APPROVAL_SCHEMA_NAME
            or record.schema_version != APPROVAL_SCHEMA_VERSION
            or record.strategy != APPROVAL_STRATEGY
            or record.activation_gate != APPROVAL_ACTIVATION_GATE
            or record.approved is not True
            or record.decision != APPROVED_DECISION
            or record.action != APPROVED_ACTION
        ):
            self._raise_consistency(
                "APPROVAL_RECORD_NOT_APPROVED",
                observed_value=f"{record.approved}:{record.decision}:{record.action}",
                required_value=f"True:{APPROVED_DECISION}:{APPROVED_ACTION}",
            )
        if any(
            getattr(record, name) is not True
            for name in self._policy.controlled_authorization_flags
        ):
            self._raise_policy("CONTROLLED_FLAGS_INCOMPLETE")
        prohibited_codes = {
            "automatic_retry_authorized": "RETRY_AUTHORIZATION_REJECTED",
            "automatic_fallback_authorized": "FALLBACK_AUTHORIZATION_REJECTED",
            "output_replacement_authorized": "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED",
        }
        for name in self._policy.prohibited_authorization_flags:
            if getattr(record, name) is not False:
                self._raise_policy(prohibited_codes[name])
        expected_finding_codes = ["EXPLICIT_HUMAN_APPROVAL_CONFIRMED"]
        if package.status == "prepared_with_warnings":
            expected_finding_codes.append("PACKAGE_WARNING_ACKNOWLEDGED")
        expected_finding_codes.append("CONTROLLED_RUNTIME_SCOPE_APPROVED")
        if [finding.code for finding in record.findings] != expected_finding_codes:
            self._raise_consistency(
                "APPROVAL_RECORD_FINGERPRINT_MISMATCH",
                observed_value="noncanonical_approval_findings",
                required_value="canonical_approval_findings",
            )
        if any(
            finding.severity != APPROVAL_FINDING_SEVERITIES.get(finding.code)
            or finding.message != APPROVAL_FINDING_MESSAGES.get(finding.code)
            for finding in record.findings
        ):
            self._raise_consistency(
                "APPROVAL_RECORD_FINGERPRINT_MISMATCH",
                observed_value="modified_approval_finding",
                required_value="canonical_approval_finding",
            )
        expected_record_fingerprint = _approval_record_fingerprint(record)
        if record.approval_record_fingerprint != expected_record_fingerprint:
            self._raise_consistency(
                "APPROVAL_RECORD_FINGERPRINT_MISMATCH",
                observed_value=record.approval_record_fingerprint,
                required_value=expected_record_fingerprint,
            )

    def _validate_scope(
        self,
        package: TranslationExecutionPackage,
        record: ExecutionApprovalRecord,
    ) -> None:
        indices = record.approved_unit_indices
        if record.approval_type not in self._policy.approval_types or not indices:
            self._raise_scope("APPROVAL_SCOPE_MISMATCH")
        if any(
            isinstance(index, bool) or not isinstance(index, int) for index in indices
        ):
            self._raise_scope("APPROVAL_SCOPE_MISMATCH")
        if len(indices) != len(set(indices)):
            self._raise_scope("APPROVED_UNIT_DUPLICATE")
        if indices != tuple(sorted(indices)):
            self._raise_scope("APPROVED_UNIT_ORDER_MISMATCH")
        if record.approved_unit_count != len(indices):
            self._raise_scope("APPROVAL_SCOPE_MISMATCH")
        if any(index < 0 or index >= package.unit_count for index in indices):
            self._raise_scope("APPROVED_UNIT_NOT_FOUND")
        if record.approval_type == "single_unit" and len(indices) != 1:
            self._raise_scope("APPROVAL_SCOPE_MISMATCH")
        if (
            record.approval_type == "full_package"
            and indices != tuple(range(package.unit_count))
        ):
            self._raise_scope("APPROVAL_SCOPE_MISMATCH")

    def _map_unit(self, submission_index: int, unit: object) -> RuntimeSubmissionUnit:
        payload = {
            "submission_index": submission_index,
            "execution_unit_index": unit.index,
            "execution_unit_id": unit.unit_id,
            "source_character_start": unit.source_character_start,
            "source_character_end": unit.source_character_end,
            "section_indices": list(unit.section_indices),
            "heading_text": unit.heading_text,
            "boundary_reason": unit.boundary_reason,
            "source_chunk_fingerprint": unit.source_chunk_fingerprint,
            "execution_unit_fingerprint": unit.execution_unit_fingerprint,
            "status": self._policy.unit_status,
            "runtime_attempt_count": self._policy.unit_runtime_attempt_count,
            "provider_request_count": self._policy.unit_provider_request_count,
            "translation_result_attached": self._policy.unit_translation_result_attached,
        }
        return RuntimeSubmissionUnit(
            submission_index=submission_index,
            execution_unit_index=unit.index,
            execution_unit_id=unit.unit_id,
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
            runtime_submission_unit_fingerprint=_sha256_payload(payload),
            status=self._policy.unit_status,
            runtime_attempt_count=self._policy.unit_runtime_attempt_count,
            provider_request_count=self._policy.unit_provider_request_count,
            translation_result_attached=self._policy.unit_translation_result_attached,
        )

    def _package_fingerprint(
        self,
        *,
        source: RuntimeSubmissionSourceReference,
        units: tuple[RuntimeSubmissionUnit, ...],
        approved_unit_indices: tuple[int, ...],
        original_execution_unit_count: int,
        approved_character_count: int,
        original_character_count: int,
        approval_coverage_ratio: float,
        status: str,
        action: str,
        findings: tuple[RuntimeSubmissionFinding, ...],
    ) -> str:
        payload = {
            "schema_name": self._policy.schema_name,
            "schema_version": self._policy.schema_version,
            "strategy": self._policy.strategy,
            "activation_gate": self._policy.activation_gate,
            "source": asdict(source),
            "approved_unit_indices": list(approved_unit_indices),
            "submission_unit_fingerprints": [
                unit.runtime_submission_unit_fingerprint for unit in units
            ],
            "submission_unit_count": len(units),
            "original_execution_unit_count": original_execution_unit_count,
            "approved_character_count": approved_character_count,
            "original_character_count": original_character_count,
            "approval_coverage_ratio": approval_coverage_ratio,
            "status": status,
            "action": action,
            "finding_codes": [finding.code for finding in findings],
            "authorization_flags": {
                **self._policy.controlled_authorization_flags,
                **self._policy.prohibited_authorization_flags,
            },
            **self._policy.execution_state,
        }
        return _sha256_payload(payload)

    def _raise_consistency(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        finding = self._finding(
            code,
            unit_index=unit_index,
            observed_value=observed_value,
            required_value=required_value,
        )
        raise RuntimeSubmissionConsistencyError(finding.message, finding=finding)

    def _raise_scope(self, code: str) -> None:
        finding = self._finding(code)
        raise RuntimeSubmissionScopeError(finding.message, finding=finding)

    def _raise_policy(self, code: str) -> None:
        finding = self._finding(code)
        raise RuntimeSubmissionPolicyError(finding.message, finding=finding)

    def _finding(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> RuntimeSubmissionFinding:
        return RuntimeSubmissionFinding(
            code=code,
            severity=self._policy.finding_severities[code],
            message=self._policy.finding_messages[code],
            unit_index=unit_index,
            observed_value=observed_value,
            required_value=required_value,
        )


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


def _execution_unit_fingerprint(unit: object) -> str:
    return _sha256_payload(
        {
            "index": unit.index,
            "unit_id": unit.unit_id,
            "chunk_index": unit.chunk_index,
            "source_character_start": unit.source_character_start,
            "source_character_end": unit.source_character_end,
            "section_indices": list(unit.section_indices),
            "heading_text": unit.heading_text,
            "boundary_reason": unit.boundary_reason,
            "source_chunk_fingerprint": unit.source_chunk_fingerprint,
            "status": unit.status,
            "attempt_count": unit.attempt_count,
            "provider_request_count": unit.provider_request_count,
            "translation_result_attached": unit.translation_result_attached,
        }
    )


def _approval_record_fingerprint(record: ExecutionApprovalRecord) -> str:
    return _sha256_payload(
        {
            "schema_name": record.schema_name,
            "schema_version": record.schema_version,
            "strategy": record.strategy,
            "activation_gate": record.activation_gate,
            "package_fingerprint": record.package_fingerprint,
            "authorization_fingerprint": record.authorization_fingerprint,
            "approval_type": record.approval_type,
            "approved_unit_indices": list(record.approved_unit_indices),
            "approved_unit_count": record.approved_unit_count,
            "provider_execution_authorized": record.provider_execution_authorized,
            "translation_execution_authorized": record.translation_execution_authorized,
            "runtime_submission_authorized": record.runtime_submission_authorized,
            "automatic_retry_authorized": record.automatic_retry_authorized,
            "automatic_fallback_authorized": record.automatic_fallback_authorized,
            "output_replacement_authorized": record.output_replacement_authorized,
            "approved": record.approved,
            "decision": record.decision,
            "action": record.action,
            "approval_statement_fingerprint": record.approval_statement_fingerprint,
            "approval_reference": record.approval_reference,
            "finding_codes": [finding.code for finding in record.findings],
        }
    )
