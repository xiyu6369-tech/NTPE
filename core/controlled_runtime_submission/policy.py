from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


SCHEMA_NAME = "ntpe.controlled_runtime_submission_package"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_controlled_runtime_submission_v1"
ACTIVATION_GATE = "controlled_runtime_submission_prepared"

REQUIRED_ACTIVATION_GATES = (
    "book_intake_layer_frozen",
    "book_preparation_pipeline_frozen",
    "translation_execution_governance_frozen",
    "translation_execution_explicitly_approved",
)

UNIT_STATUS = "queued_for_controlled_submission"
PACKAGE_STATUS = "prepared_for_controlled_submission"
PACKAGE_WARNING_STATUS = "prepared_for_controlled_submission_with_warnings"
BLOCKED_STATUS = "blocked"
HOLD_ACTION = "hold_for_runtime_adapter"
MANUAL_REVIEW_ACTION = "manual_review"
REJECT_ACTION = "reject"

APPROVAL_TYPES = ("single_unit", "selected_units", "full_package")
STATUS_ACTIONS = MappingProxyType(
    {
        PACKAGE_STATUS: HOLD_ACTION,
        PACKAGE_WARNING_STATUS: HOLD_ACTION,
        BLOCKED_STATUS: REJECT_ACTION,
    }
)

CONTROLLED_AUTHORIZATION_FLAGS = MappingProxyType(
    {
        "provider_execution_authorized": True,
        "translation_execution_authorized": True,
        "runtime_submission_authorized": True,
    }
)
PROHIBITED_AUTHORIZATION_FLAGS = MappingProxyType(
    {
        "automatic_retry_authorized": False,
        "automatic_fallback_authorized": False,
        "output_replacement_authorized": False,
    }
)
EXECUTION_STATE = MappingProxyType(
    {
        "runtime_submission_executed": False,
        "provider_requests_executed": 0,
        "translation_executions_completed": 0,
    }
)

FINDING_CODES = (
    "CONTROLLED_RUNTIME_SUBMISSION_PREPARED",
    "PARTIAL_SCOPE_SUBMISSION",
    "FULL_PACKAGE_SUBMISSION",
    "PACKAGE_WARNING_PROPAGATED",
    "PACKAGE_FINGERPRINT_MISMATCH",
    "AUTHORIZATION_FINGERPRINT_MISMATCH",
    "APPROVAL_RECORD_FINGERPRINT_MISMATCH",
    "APPROVAL_RECORD_NOT_APPROVED",
    "APPROVAL_SCOPE_MISMATCH",
    "APPROVED_UNIT_NOT_FOUND",
    "APPROVED_UNIT_ORDER_MISMATCH",
    "APPROVED_UNIT_DUPLICATE",
    "EXECUTION_UNIT_ALREADY_EXECUTED",
    "EXECUTION_UNIT_TEXT_MISMATCH",
    "EXECUTION_UNIT_FINGERPRINT_MISMATCH",
    "EXECUTION_UNIT_OFFSET_INVALID",
    "CONTROLLED_FLAGS_INCOMPLETE",
    "RETRY_AUTHORIZATION_REJECTED",
    "FALLBACK_AUTHORIZATION_REJECTED",
    "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED",
    "RUNTIME_SUBMISSION_NOT_EXECUTED",
    "PROVIDER_REQUEST_COUNT_ZERO",
    "TRANSLATION_EXECUTION_COUNT_ZERO",
)
FINDING_SEVERITIES = MappingProxyType(
    {
        code: (
            "info"
            if code
            in {
                "CONTROLLED_RUNTIME_SUBMISSION_PREPARED",
                "FULL_PACKAGE_SUBMISSION",
                "RUNTIME_SUBMISSION_NOT_EXECUTED",
                "PROVIDER_REQUEST_COUNT_ZERO",
                "TRANSLATION_EXECUTION_COUNT_ZERO",
            }
            else "warning"
            if code in {"PARTIAL_SCOPE_SUBMISSION", "PACKAGE_WARNING_PROPAGATED"}
            else "blocking"
        )
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "CONTROLLED_RUNTIME_SUBMISSION_PREPARED": "Approved units were prepared for controlled runtime submission.",
        "PARTIAL_SCOPE_SUBMISSION": "Only the explicitly approved portion of the execution package is included.",
        "FULL_PACKAGE_SUBMISSION": "Every execution unit is included in the approved submission scope.",
        "PACKAGE_WARNING_PROPAGATED": "Warnings from the approved execution package remain visible.",
        "PACKAGE_FINGERPRINT_MISMATCH": "The execution package fingerprint chain is inconsistent.",
        "AUTHORIZATION_FINGERPRINT_MISMATCH": "The authorization decision fingerprint chain is inconsistent.",
        "APPROVAL_RECORD_FINGERPRINT_MISMATCH": "The approval record fingerprint is not canonical.",
        "APPROVAL_RECORD_NOT_APPROVED": "The approval record is not eligible for controlled runtime submission.",
        "APPROVAL_SCOPE_MISMATCH": "The approval type and approved unit scope are inconsistent.",
        "APPROVED_UNIT_NOT_FOUND": "An approved execution unit does not exist in the package.",
        "APPROVED_UNIT_ORDER_MISMATCH": "Approved execution unit indices are not in canonical order.",
        "APPROVED_UNIT_DUPLICATE": "The approval scope contains a duplicate execution unit index.",
        "EXECUTION_UNIT_ALREADY_EXECUTED": "An approved execution unit is no longer in its initial prepared state.",
        "EXECUTION_UNIT_TEXT_MISMATCH": "Execution unit text or character metadata is inconsistent.",
        "EXECUTION_UNIT_FINGERPRINT_MISMATCH": "An execution unit fingerprint is not canonical.",
        "EXECUTION_UNIT_OFFSET_INVALID": "An execution unit has invalid source offsets.",
        "CONTROLLED_FLAGS_INCOMPLETE": "All controlled execution authorization flags must be true.",
        "RETRY_AUTHORIZATION_REJECTED": "Automatic retry authorization is prohibited.",
        "FALLBACK_AUTHORIZATION_REJECTED": "Automatic fallback authorization is prohibited.",
        "OUTPUT_REPLACEMENT_AUTHORIZATION_REJECTED": "Output replacement authorization is prohibited.",
        "RUNTIME_SUBMISSION_NOT_EXECUTED": "The runtime submission package has not been executed.",
        "PROVIDER_REQUEST_COUNT_ZERO": "No provider request was executed.",
        "TRANSLATION_EXECUTION_COUNT_ZERO": "No translation execution was completed.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)


@dataclass(frozen=True)
class ControlledRuntimeSubmissionPolicy:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    required_activation_gates: tuple[str, ...]
    unit_status: str
    unit_runtime_attempt_count: int
    unit_provider_request_count: int
    unit_translation_result_attached: bool
    approval_types: tuple[str, ...]
    status_actions: Mapping[str, str]
    controlled_authorization_flags: Mapping[str, bool]
    prohibited_authorization_flags: Mapping[str, bool]
    execution_state: Mapping[str, bool | int]
    finding_codes: tuple[str, ...]
    finding_severities: Mapping[str, str]
    finding_messages: Mapping[str, str]
    finding_order: Mapping[str, int]


DEFAULT_POLICY = ControlledRuntimeSubmissionPolicy(
    schema_name=SCHEMA_NAME,
    schema_version=SCHEMA_VERSION,
    strategy=STRATEGY,
    activation_gate=ACTIVATION_GATE,
    required_activation_gates=REQUIRED_ACTIVATION_GATES,
    unit_status=UNIT_STATUS,
    unit_runtime_attempt_count=0,
    unit_provider_request_count=0,
    unit_translation_result_attached=False,
    approval_types=APPROVAL_TYPES,
    status_actions=STATUS_ACTIONS,
    controlled_authorization_flags=CONTROLLED_AUTHORIZATION_FLAGS,
    prohibited_authorization_flags=PROHIBITED_AUTHORIZATION_FLAGS,
    execution_state=EXECUTION_STATE,
    finding_codes=FINDING_CODES,
    finding_severities=FINDING_SEVERITIES,
    finding_messages=FINDING_MESSAGES,
    finding_order=FINDING_ORDER,
)
