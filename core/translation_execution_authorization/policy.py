from __future__ import annotations

from types import MappingProxyType

from core.translation_execution_package.policy import (
    ACTIVATION_GATE as PACKAGE_ACTIVATION_GATE,
    SCHEMA_NAME as PACKAGE_SCHEMA_NAME,
    SCHEMA_VERSION as PACKAGE_SCHEMA_VERSION,
    STRATEGY as PACKAGE_STRATEGY,
)

from .models import ExecutionAuthorizationPolicy


SCHEMA_NAME = "ntpe.translation_execution_authorization_decision"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_fail_closed_authorization_v1"
POLICY_NAME = "ntpe.translation_execution_authorization"
POLICY_VERSION = "1.0"

DENIED_DECISION = "denied"
AUTHORIZED_DECISION = "authorized"
HOLD_ACTION = "hold_for_explicit_authorization"
MANUAL_REVIEW_ACTION = "manual_review"
REJECT_ACTION = "reject"
SUBMIT_ACTION = "submit_to_controlled_runtime"

PACKAGE_STATUS_ACTIONS = MappingProxyType(
    {
        "prepared": "hold_for_execution_authorization",
        "prepared_with_warnings": "hold_for_execution_authorization",
        "blocked": "reject",
    }
)
DECISION_ACTIONS = MappingProxyType(
    {
        "authorized": SUBMIT_ACTION,
        "denied_prepared": HOLD_ACTION,
        "denied_prepared_with_warnings": MANUAL_REVIEW_ACTION,
        "denied_invalid": REJECT_ACTION,
    }
)

EXECUTION_FLAG_NAMES = (
    "provider_execution_authorized",
    "translation_execution_authorized",
    "runtime_submission_authorized",
    "automatic_retry_authorized",
    "automatic_fallback_authorized",
    "output_replacement_authorized",
)
ALLOW_FLAG_NAMES = (
    "allow_prepared",
    "allow_prepared_with_warnings",
    "allow_manual_review",
    "allow_blocked",
)

FINDING_CODES = (
    "EXPLICIT_AUTHORIZATION_REQUIRED",
    "PACKAGE_SCHEMA_MISMATCH",
    "PACKAGE_VERSION_MISMATCH",
    "PACKAGE_STRATEGY_MISMATCH",
    "PACKAGE_ACTIVATION_GATE_MISMATCH",
    "PACKAGE_STATUS_NOT_ELIGIBLE",
    "PACKAGE_ACTION_MISMATCH",
    "PACKAGE_FINGERPRINT_INVALID",
    "PACKAGE_CONTENT_MISMATCH",
    "PACKAGE_UNIT_COUNT_MISMATCH",
    "PACKAGE_OFFSET_GAP",
    "PACKAGE_OFFSET_OVERLAP",
    "PACKAGE_ALREADY_EXECUTED",
    "PACKAGE_PROVIDER_REQUEST_DETECTED",
    "PACKAGE_TRANSLATION_RESULT_DETECTED",
    "PACKAGE_AUTHORIZATION_FLAG_TAMPERED",
    "POLICY_RELAXATION_REJECTED",
    "PROVIDER_EXECUTION_NOT_AUTHORIZED",
    "TRANSLATION_EXECUTION_NOT_AUTHORIZED",
    "RUNTIME_SUBMISSION_NOT_AUTHORIZED",
    "AUTOMATIC_RETRY_NOT_AUTHORIZED",
    "AUTOMATIC_FALLBACK_NOT_AUTHORIZED",
    "OUTPUT_REPLACEMENT_NOT_AUTHORIZED",
    "MANUAL_REVIEW_REQUIRED",
    "BLOCKED_PACKAGE_REJECTED",
)
FINDING_SEVERITIES = MappingProxyType(
    {
        code: (
            "info"
            if code
            in {
                "EXPLICIT_AUTHORIZATION_REQUIRED",
                "PROVIDER_EXECUTION_NOT_AUTHORIZED",
                "TRANSLATION_EXECUTION_NOT_AUTHORIZED",
                "RUNTIME_SUBMISSION_NOT_AUTHORIZED",
                "AUTOMATIC_RETRY_NOT_AUTHORIZED",
                "AUTOMATIC_FALLBACK_NOT_AUTHORIZED",
                "OUTPUT_REPLACEMENT_NOT_AUTHORIZED",
            }
            else "manual_review"
            if code == "MANUAL_REVIEW_REQUIRED"
            else "blocking"
        )
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "EXPLICIT_AUTHORIZATION_REQUIRED": "Explicit human authorization is required before execution.",
        "PACKAGE_SCHEMA_MISMATCH": "Execution package schema name does not match the required contract.",
        "PACKAGE_VERSION_MISMATCH": "Execution package schema version does not match the required contract.",
        "PACKAGE_STRATEGY_MISMATCH": "Execution package strategy does not match the required contract.",
        "PACKAGE_ACTIVATION_GATE_MISMATCH": "Execution package activation gate is invalid.",
        "PACKAGE_STATUS_NOT_ELIGIBLE": "Execution package status is not eligible for authorization evaluation.",
        "PACKAGE_ACTION_MISMATCH": "Execution package status and action are inconsistent.",
        "PACKAGE_FINGERPRINT_INVALID": "Execution package fingerprint is invalid or inconsistent.",
        "PACKAGE_CONTENT_MISMATCH": "Execution package content and character metadata are inconsistent.",
        "PACKAGE_UNIT_COUNT_MISMATCH": "Execution package unit count is inconsistent.",
        "PACKAGE_OFFSET_GAP": "Execution package unit offsets contain a gap.",
        "PACKAGE_OFFSET_OVERLAP": "Execution package unit offsets overlap.",
        "PACKAGE_ALREADY_EXECUTED": "An execution unit is no longer in its initial prepared state.",
        "PACKAGE_PROVIDER_REQUEST_DETECTED": "An execution unit records a provider request.",
        "PACKAGE_TRANSLATION_RESULT_DETECTED": "An execution unit already has a translation result attached.",
        "PACKAGE_AUTHORIZATION_FLAG_TAMPERED": "An execution package authorization flag was enabled.",
        "POLICY_RELAXATION_REJECTED": "The injected policy attempts to relax the fail-closed authorization boundary.",
        "PROVIDER_EXECUTION_NOT_AUTHORIZED": "Provider execution remains unauthorized.",
        "TRANSLATION_EXECUTION_NOT_AUTHORIZED": "Translation execution remains unauthorized.",
        "RUNTIME_SUBMISSION_NOT_AUTHORIZED": "Runtime submission remains unauthorized.",
        "AUTOMATIC_RETRY_NOT_AUTHORIZED": "Automatic retry remains unauthorized.",
        "AUTOMATIC_FALLBACK_NOT_AUTHORIZED": "Automatic fallback remains unauthorized.",
        "OUTPUT_REPLACEMENT_NOT_AUTHORIZED": "Output replacement remains unauthorized.",
        "MANUAL_REVIEW_REQUIRED": "A warning-bearing package requires manual review.",
        "BLOCKED_PACKAGE_REJECTED": "A blocked package cannot be evaluated for execution authorization.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)

DEFAULT_POLICY = ExecutionAuthorizationPolicy(
    policy_name=POLICY_NAME,
    policy_version=POLICY_VERSION,
    required_package_schema_name=PACKAGE_SCHEMA_NAME,
    required_package_schema_version=PACKAGE_SCHEMA_VERSION,
    required_package_activation_gate=PACKAGE_ACTIVATION_GATE,
    allow_prepared=False,
    allow_prepared_with_warnings=False,
    allow_manual_review=False,
    allow_blocked=False,
    provider_execution_authorized=False,
    translation_execution_authorized=False,
    runtime_submission_authorized=False,
    automatic_retry_authorized=False,
    automatic_fallback_authorized=False,
    output_replacement_authorized=False,
    require_explicit_human_approval=True,
)

