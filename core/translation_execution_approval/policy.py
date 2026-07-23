from __future__ import annotations

from types import MappingProxyType


SCHEMA_NAME = "ntpe.translation_execution_approval_record"
SCHEMA_VERSION = "1.0"
STRATEGY = "explicit_human_scoped_execution_approval_v1"
ACTIVATION_GATE = "translation_execution_explicitly_approved"

APPROVAL_TYPES = ("single_unit", "selected_units", "full_package")
CONFIRMATION_TOKEN = "APPROVE_CONTROLLED_TRANSLATION_EXECUTION"
WARNING_ACKNOWLEDGEMENT_TOKEN = "ACKNOWLEDGE_PACKAGE_WARNINGS"
MINIMUM_STATEMENT_LENGTH = 12
MAXIMUM_REFERENCE_LENGTH = 128

PACKAGE_STATUSES = ("prepared", "prepared_with_warnings")
PACKAGE_ACTION = "hold_for_execution_authorization"
APPROVED_DECISION = "approved"
APPROVED_ACTION = "eligible_for_controlled_runtime"
REJECTED_DECISION = "rejected"
HOLD_ACTION = "hold_for_manual_correction"
REJECT_ACTION = "reject"

REQUIRED_REQUEST_FLAGS = (
    "approve_provider_execution",
    "approve_translation_execution",
    "approve_runtime_submission",
)
PROHIBITED_REQUEST_FLAGS = (
    "approve_automatic_retry",
    "approve_automatic_fallback",
    "approve_output_replacement",
)
PACKAGE_AUTHORIZATION_FLAGS = (
    "provider_execution_authorized",
    "translation_execution_authorized",
    "runtime_submission_authorized",
    "automatic_retry_authorized",
    "automatic_fallback_authorized",
    "output_replacement_authorized",
)

FINDING_CODES = (
    "EXPLICIT_HUMAN_APPROVAL_CONFIRMED",
    "PACKAGE_WARNING_ACKNOWLEDGED",
    "PACKAGE_WARNING_ACKNOWLEDGEMENT_REQUIRED",
    "APPROVAL_STATEMENT_MISSING",
    "APPROVAL_CONFIRMATION_TOKEN_MISSING",
    "APPROVAL_REFERENCE_MISSING",
    "APPROVAL_REFERENCE_INVALID",
    "APPROVAL_TYPE_INVALID",
    "APPROVAL_SCOPE_EMPTY",
    "APPROVAL_SCOPE_DUPLICATE_INDEX",
    "APPROVAL_SCOPE_UNSORTED",
    "APPROVAL_SCOPE_OUT_OF_RANGE",
    "APPROVAL_SCOPE_TYPE_MISMATCH",
    "FULL_PACKAGE_SCOPE_INCOMPLETE",
    "SINGLE_UNIT_SCOPE_INVALID",
    "PACKAGE_FINGERPRINT_MISMATCH",
    "AUTHORIZATION_FINGERPRINT_MISMATCH",
    "AUTHORIZATION_DECISION_INVALID",
    "AUTHORIZATION_HUMAN_APPROVAL_NOT_REQUIRED",
    "PACKAGE_STATE_INVALID",
    "PACKAGE_ALREADY_EXECUTED",
    "PACKAGE_AUTHORIZATION_FLAG_TAMPERED",
    "RETRY_AUTHORIZATION_REJECTED",
    "FALLBACK_AUTHORIZATION_REJECTED",
    "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED",
    "CONTROLLED_EXECUTION_AUTHORIZATION_INCOMPLETE",
    "CONTROLLED_RUNTIME_SCOPE_APPROVED",
)
FINDING_SEVERITIES = MappingProxyType(
    {
        code: (
            "info"
            if code
            in {
                "EXPLICIT_HUMAN_APPROVAL_CONFIRMED",
                "PACKAGE_WARNING_ACKNOWLEDGED",
                "CONTROLLED_RUNTIME_SCOPE_APPROVED",
            }
            else "blocking"
        )
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "EXPLICIT_HUMAN_APPROVAL_CONFIRMED": "Explicit human execution approval was confirmed.",
        "PACKAGE_WARNING_ACKNOWLEDGED": "Package warnings were explicitly acknowledged.",
        "PACKAGE_WARNING_ACKNOWLEDGEMENT_REQUIRED": "Warning-bearing packages require explicit warning acknowledgement.",
        "APPROVAL_STATEMENT_MISSING": "An explicit approval statement meeting the minimum length is required.",
        "APPROVAL_CONFIRMATION_TOKEN_MISSING": "The fixed controlled-execution confirmation token is required.",
        "APPROVAL_REFERENCE_MISSING": "A caller-provided approval reference is required.",
        "APPROVAL_REFERENCE_INVALID": "The approval reference contains prohibited environment or path metadata.",
        "APPROVAL_TYPE_INVALID": "The requested approval type is invalid.",
        "APPROVAL_SCOPE_EMPTY": "The approval scope must contain at least one unit.",
        "APPROVAL_SCOPE_DUPLICATE_INDEX": "Approval scope indices must be unique.",
        "APPROVAL_SCOPE_UNSORTED": "Approval scope indices must be in ascending order.",
        "APPROVAL_SCOPE_OUT_OF_RANGE": "An approval scope index is outside the package.",
        "APPROVAL_SCOPE_TYPE_MISMATCH": "Every approval scope index must be an integer and not a boolean.",
        "FULL_PACKAGE_SCOPE_INCOMPLETE": "Full-package approval must cover every package unit exactly.",
        "SINGLE_UNIT_SCOPE_INVALID": "Single-unit approval must contain exactly one unit index.",
        "PACKAGE_FINGERPRINT_MISMATCH": "The approval evidence is not bound to this execution package fingerprint.",
        "AUTHORIZATION_FINGERPRINT_MISMATCH": "The approval evidence is not bound to the canonical authorization fingerprint.",
        "AUTHORIZATION_DECISION_INVALID": "The authorization decision is not the canonical denied decision.",
        "AUTHORIZATION_HUMAN_APPROVAL_NOT_REQUIRED": "The authorization decision does not require explicit human approval.",
        "PACKAGE_STATE_INVALID": "The execution package state is not eligible for approval.",
        "PACKAGE_ALREADY_EXECUTED": "An execution unit is no longer in its initial prepared state.",
        "PACKAGE_AUTHORIZATION_FLAG_TAMPERED": "An execution package authorization flag was enabled.",
        "RETRY_AUTHORIZATION_REJECTED": "Automatic retry cannot be approved by this stage.",
        "FALLBACK_AUTHORIZATION_REJECTED": "Automatic fallback cannot be approved by this stage.",
        "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED": "Output replacement cannot be approved by this stage.",
        "CONTROLLED_EXECUTION_AUTHORIZATION_INCOMPLETE": "Provider, translation, and runtime submission approval must all be explicit.",
        "CONTROLLED_RUNTIME_SCOPE_APPROVED": "The exact requested unit scope is eligible for one controlled runtime execution.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)
