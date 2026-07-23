from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict

from core.translation_execution_authorization import (
    ExecutionAuthorizationDecision,
    TranslationExecutionAuthorizationError,
    TranslationExecutionAuthorizationEvaluator,
)
from core.translation_execution_authorization.policy import (
    SCHEMA_NAME as AUTHORIZATION_SCHEMA_NAME,
    SCHEMA_VERSION as AUTHORIZATION_SCHEMA_VERSION,
    STRATEGY as AUTHORIZATION_STRATEGY,
)
from core.translation_execution_package import TranslationExecutionPackage

from .errors import (
    ExecutionApprovalConsistencyError,
    ExecutionApprovalPolicyError,
    ExecutionApprovalScopeError,
    InvalidExecutionApprovalInputError,
    InvalidHumanApprovalRequestError,
)
from .models import (
    ExecutionApprovalFinding,
    ExecutionApprovalRecord,
    ExplicitHumanApprovalRequest,
)
from .policy import (
    ACTIVATION_GATE,
    APPROVAL_TYPES,
    APPROVED_ACTION,
    APPROVED_DECISION,
    CONFIRMATION_TOKEN,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    MAXIMUM_REFERENCE_LENGTH,
    MINIMUM_STATEMENT_LENGTH,
    PACKAGE_ACTION,
    PACKAGE_AUTHORIZATION_FLAGS,
    PACKAGE_STATUSES,
    PROHIBITED_REQUEST_FLAGS,
    REQUIRED_REQUEST_FLAGS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STRATEGY,
    WARNING_ACKNOWLEDGEMENT_TOKEN,
)


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class _FindingCollector:
    def __init__(self) -> None:
        self._items: dict[str, ExecutionApprovalFinding] = {}

    def add(
        self,
        code: str,
        *,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        self._items.setdefault(
            code,
            _finding(code, observed_value, required_value),
        )

    def ordered(self) -> tuple[ExecutionApprovalFinding, ...]:
        return tuple(
            sorted(self._items.values(), key=lambda item: FINDING_ORDER[item.code])
        )


class TranslationExecutionApprover:
    """Create an immutable scoped approval record without executing work."""

    def approve(
        self,
        *,
        package: TranslationExecutionPackage,
        authorization_decision: ExecutionAuthorizationDecision,
        approval_request: ExplicitHumanApprovalRequest,
    ) -> ExecutionApprovalRecord:
        self._validate_input_types(package, authorization_decision, approval_request)
        self._validate_package_and_decision(package, authorization_decision)
        self._validate_request_bindings(
            package, authorization_decision, approval_request
        )
        self._validate_statement_and_reference(package, approval_request)
        self._validate_authorization_flags(approval_request)
        self._validate_scope(package, approval_request)

        findings = _FindingCollector()
        findings.add("EXPLICIT_HUMAN_APPROVAL_CONFIRMED")
        if package.status == "prepared_with_warnings":
            findings.add("PACKAGE_WARNING_ACKNOWLEDGED")
        findings.add(
            "CONTROLLED_RUNTIME_SCOPE_APPROVED",
            observed_value=len(approval_request.approved_unit_indices),
            required_value=len(approval_request.approved_unit_indices),
        )
        ordered_findings = findings.ordered()
        statement_fingerprint = _sha256_text(approval_request.approval_statement)
        fingerprint = _record_fingerprint(
            package_fingerprint=package.execution_package_fingerprint,
            authorization_fingerprint=authorization_decision.authorization_fingerprint,
            request=approval_request,
            statement_fingerprint=statement_fingerprint,
            findings=ordered_findings,
        )
        return ExecutionApprovalRecord(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            strategy=STRATEGY,
            activation_gate=ACTIVATION_GATE,
            package_fingerprint=package.execution_package_fingerprint,
            authorization_fingerprint=authorization_decision.authorization_fingerprint,
            approval_type=approval_request.approval_type,
            approved_unit_indices=approval_request.approved_unit_indices,
            approved_unit_count=len(approval_request.approved_unit_indices),
            provider_execution_authorized=True,
            translation_execution_authorized=True,
            runtime_submission_authorized=True,
            automatic_retry_authorized=False,
            automatic_fallback_authorized=False,
            output_replacement_authorized=False,
            approved=True,
            decision=APPROVED_DECISION,
            action=APPROVED_ACTION,
            approval_statement_fingerprint=statement_fingerprint,
            approval_reference=approval_request.approval_reference,
            findings=ordered_findings,
            summary=(
                f"Explicit approval recorded for {len(approval_request.approved_unit_indices)} "
                "unit(s); no execution was performed."
            ),
            approval_record_fingerprint=fingerprint,
        )

    @staticmethod
    def _validate_input_types(
        package: object, decision: object, request: object
    ) -> None:
        if not isinstance(package, TranslationExecutionPackage):
            raise InvalidExecutionApprovalInputError(
                "package must be a TranslationExecutionPackage"
            )
        if not isinstance(decision, ExecutionAuthorizationDecision):
            raise InvalidExecutionApprovalInputError(
                "authorization_decision must be an ExecutionAuthorizationDecision"
            )
        if not isinstance(request, ExplicitHumanApprovalRequest):
            raise InvalidExecutionApprovalInputError(
                "approval_request must be an ExplicitHumanApprovalRequest"
            )

    @staticmethod
    def _validate_package_and_decision(
        package: TranslationExecutionPackage,
        decision: ExecutionAuthorizationDecision,
    ) -> None:
        try:
            expected = TranslationExecutionAuthorizationEvaluator().evaluate(package)
        except TranslationExecutionAuthorizationError as error:
            code = (
                "PACKAGE_ALREADY_EXECUTED"
                if getattr(getattr(error, "finding", None), "code", "")
                in {
                    "PACKAGE_ALREADY_EXECUTED",
                    "PACKAGE_PROVIDER_REQUEST_DETECTED",
                    "PACKAGE_TRANSLATION_RESULT_DETECTED",
                }
                else "PACKAGE_AUTHORIZATION_FLAG_TAMPERED"
                if getattr(getattr(error, "finding", None), "code", "")
                == "PACKAGE_AUTHORIZATION_FLAG_TAMPERED"
                else "PACKAGE_STATE_INVALID"
            )
            raise ExecutionApprovalConsistencyError(
                FINDING_MESSAGES[code], finding=_finding(code)
            ) from error
        if package.status not in PACKAGE_STATUSES or package.action != PACKAGE_ACTION:
            _raise_consistency(
                "PACKAGE_STATE_INVALID",
                f"{package.status}:{package.action}",
                f"{PACKAGE_STATUSES}:{PACKAGE_ACTION}",
            )
        if decision.package_fingerprint != package.execution_package_fingerprint:
            _raise_consistency(
                "PACKAGE_FINGERPRINT_MISMATCH",
                decision.package_fingerprint,
                package.execution_package_fingerprint,
            )
        if decision.requires_human_approval is not True:
            _raise_consistency(
                "AUTHORIZATION_HUMAN_APPROVAL_NOT_REQUIRED",
                decision.requires_human_approval,
                True,
            )
        if (
            decision.schema_name != AUTHORIZATION_SCHEMA_NAME
            or decision.schema_version != AUTHORIZATION_SCHEMA_VERSION
            or decision.strategy != AUTHORIZATION_STRATEGY
            or decision.authorized is not False
            or decision.decision != "denied"
            or any(
                getattr(decision, name) is not False
                for name in PACKAGE_AUTHORIZATION_FLAGS
            )
            or "EXPLICIT_AUTHORIZATION_REQUIRED"
            not in {finding.code for finding in decision.findings}
        ):
            _raise_consistency(
                "AUTHORIZATION_DECISION_INVALID",
                decision.decision,
                "denied",
            )
        if decision.authorization_fingerprint != expected.authorization_fingerprint:
            _raise_consistency(
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
                decision.authorization_fingerprint,
                expected.authorization_fingerprint,
            )
        if decision != expected:
            _raise_consistency(
                "AUTHORIZATION_DECISION_INVALID",
                "noncanonical",
                "canonical_denied_decision",
            )

    @staticmethod
    def _validate_request_bindings(
        package: TranslationExecutionPackage,
        decision: ExecutionAuthorizationDecision,
        request: ExplicitHumanApprovalRequest,
    ) -> None:
        if (
            not _HEX_64.fullmatch(request.approved_package_fingerprint)
            or request.approved_package_fingerprint
            != package.execution_package_fingerprint
        ):
            _raise_request(
                "PACKAGE_FINGERPRINT_MISMATCH",
                request.approved_package_fingerprint,
                package.execution_package_fingerprint,
            )
        if (
            not _HEX_64.fullmatch(request.approved_authorization_fingerprint)
            or request.approved_authorization_fingerprint
            != decision.authorization_fingerprint
        ):
            _raise_request(
                "AUTHORIZATION_FINGERPRINT_MISMATCH",
                request.approved_authorization_fingerprint,
                decision.authorization_fingerprint,
            )

    @staticmethod
    def _validate_statement_and_reference(
        package: TranslationExecutionPackage,
        request: ExplicitHumanApprovalRequest,
    ) -> None:
        if (
            not isinstance(request.approval_statement, str)
            or len(request.approval_statement.strip()) < MINIMUM_STATEMENT_LENGTH
        ):
            _raise_request(
                "APPROVAL_STATEMENT_MISSING",
                0
                if not isinstance(request.approval_statement, str)
                else len(request.approval_statement.strip()),
                MINIMUM_STATEMENT_LENGTH,
            )
        if CONFIRMATION_TOKEN not in request.approval_statement:
            _raise_request(
                "APPROVAL_CONFIRMATION_TOKEN_MISSING",
                False,
                CONFIRMATION_TOKEN,
            )
        if (
            package.status == "prepared_with_warnings"
            and WARNING_ACKNOWLEDGEMENT_TOKEN not in request.approval_statement
        ):
            _raise_request(
                "PACKAGE_WARNING_ACKNOWLEDGEMENT_REQUIRED",
                False,
                WARNING_ACKNOWLEDGEMENT_TOKEN,
            )
        reference = request.approval_reference
        if not isinstance(reference, str) or not reference.strip():
            _raise_request("APPROVAL_REFERENCE_MISSING", False, True)
        if (
            reference != reference.strip()
            or len(reference) > MAXIMUM_REFERENCE_LENGTH
            or _UUID.fullmatch(reference)
            or any(character in reference for character in ("/", "\\", ":", "@"))
            or not all(
                character.isalnum() or character in "._-" for character in reference
            )
        ):
            _raise_request(
                "APPROVAL_REFERENCE_INVALID",
                "prohibited_format",
                "caller_reference",
            )

    @staticmethod
    def _validate_authorization_flags(
        request: ExplicitHumanApprovalRequest,
    ) -> None:
        prohibited_codes = {
            "approve_automatic_retry": "RETRY_AUTHORIZATION_REJECTED",
            "approve_automatic_fallback": "FALLBACK_AUTHORIZATION_REJECTED",
            "approve_output_replacement": "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED",
        }
        for name in PROHIBITED_REQUEST_FLAGS:
            if getattr(request, name) is not False:
                code = prohibited_codes[name]
                finding = _finding(code, getattr(request, name), False)
                raise ExecutionApprovalPolicyError(
                    finding.message, finding=finding
                )
        if any(getattr(request, name) is not True for name in REQUIRED_REQUEST_FLAGS):
            _raise_request(
                "CONTROLLED_EXECUTION_AUTHORIZATION_INCOMPLETE",
                False,
                True,
            )

    @staticmethod
    def _validate_scope(
        package: TranslationExecutionPackage,
        request: ExplicitHumanApprovalRequest,
    ) -> None:
        if request.approval_type not in APPROVAL_TYPES:
            _raise_scope(
                "APPROVAL_TYPE_INVALID", request.approval_type, APPROVAL_TYPES
            )
        indices = request.approved_unit_indices
        if not indices:
            _raise_scope("APPROVAL_SCOPE_EMPTY", 0, 1)
        if any(isinstance(index, bool) or not isinstance(index, int) for index in indices):
            _raise_scope(
                "APPROVAL_SCOPE_TYPE_MISMATCH", "non_integer", "integer"
            )
        if len(set(indices)) != len(indices):
            _raise_scope(
                "APPROVAL_SCOPE_DUPLICATE_INDEX", len(indices), len(set(indices))
            )
        if tuple(sorted(indices)) != indices:
            _raise_scope("APPROVAL_SCOPE_UNSORTED", "unsorted", "ascending")
        if package.unit_count <= 0 or any(
            index < 0 or index >= package.unit_count for index in indices
        ):
            _raise_scope(
                "APPROVAL_SCOPE_OUT_OF_RANGE",
                str(indices),
                f"0..{package.unit_count - 1}",
            )
        if request.approval_type == "single_unit" and len(indices) != 1:
            _raise_scope("SINGLE_UNIT_SCOPE_INVALID", len(indices), 1)
        if (
            request.approval_type == "full_package"
            and indices != tuple(range(package.unit_count))
        ):
            _raise_scope(
                "FULL_PACKAGE_SCOPE_INCOMPLETE",
                len(indices),
                package.unit_count,
            )


def _finding(
    code: str,
    observed_value: str | int | float | bool | None = None,
    required_value: str | int | float | bool | None = None,
) -> ExecutionApprovalFinding:
    return ExecutionApprovalFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=FINDING_MESSAGES[code],
        observed_value=observed_value,
        required_value=required_value,
    )


def _raise_request(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: str | int | float | bool | None,
) -> None:
    finding = _finding(code, observed_value, required_value)
    raise InvalidHumanApprovalRequestError(finding.message, finding=finding)


def _raise_scope(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: object,
) -> None:
    finding = _finding(code, observed_value, str(required_value))
    raise ExecutionApprovalScopeError(finding.message, finding=finding)


def _raise_consistency(
    code: str,
    observed_value: str | int | float | bool | None,
    required_value: str | int | float | bool | None,
) -> None:
    finding = _finding(code, observed_value, required_value)
    raise ExecutionApprovalConsistencyError(finding.message, finding=finding)


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _record_fingerprint(
    *,
    package_fingerprint: str,
    authorization_fingerprint: str,
    request: ExplicitHumanApprovalRequest,
    statement_fingerprint: str,
    findings: tuple[ExecutionApprovalFinding, ...],
) -> str:
    payload = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "strategy": STRATEGY,
        "activation_gate": ACTIVATION_GATE,
        "package_fingerprint": package_fingerprint,
        "authorization_fingerprint": authorization_fingerprint,
        "approval_type": request.approval_type,
        "approved_unit_indices": list(request.approved_unit_indices),
        "approved_unit_count": len(request.approved_unit_indices),
        "provider_execution_authorized": True,
        "translation_execution_authorized": True,
        "runtime_submission_authorized": True,
        "automatic_retry_authorized": False,
        "automatic_fallback_authorized": False,
        "output_replacement_authorized": False,
        "approved": True,
        "decision": APPROVED_DECISION,
        "action": APPROVED_ACTION,
        "approval_statement_fingerprint": statement_fingerprint,
        "approval_reference": request.approval_reference,
        "finding_codes": [finding.code for finding in findings],
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
