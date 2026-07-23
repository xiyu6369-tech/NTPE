from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_execution_authorization_request"
REQUEST_SCHEMA_VERSION = "1.0"
DECISION_SCHEMA_NAME = "ntpe.controlled_runtime_execution_authorization_decision"
DECISION_SCHEMA_VERSION = "1.0"

FROZEN_COMPONENT = "ntpe.controlled_runtime_preparation"
FROZEN_VERSION = "5.4"
FROZEN_ACTIVATION_GATE = "controlled_runtime_preparation_frozen"
PLAN_SCHEMA_NAME = "ntpe.controlled_runtime_execution_plan"
PLAN_SCHEMA_VERSION = "1.0"
PLAN_STRATEGY = "deterministic_single_unit_execution_plan_v1"
PLAN_ACTIVATION_GATE = "controlled_runtime_execution_plan_prepared"
PLAN_ACTION = "hold_for_explicit_runtime_execution_enablement"
PLAN_STATUSES = ("planned", "planned_with_warnings")
STEP_STATUS = "planned_not_executed"

AUTHORIZED_STATUS = "authorized_not_executed"
REJECTED_STATUS = "rejected"
INVALID_REQUEST_STATUS = "invalid_request"
FROZEN_CONTRACT_MISMATCH_STATUS = "frozen_contract_mismatch"

RETAIN_ACTION = "retain_for_controlled_execution_review"
CORRECT_ACTION = "correct_request"
REJECT_ACTION = "reject"
REBUILD_ACTION = "rebuild_from_frozen_preparation"


@dataclass(frozen=True)
class ControlledRuntimeExecutionAuthorizationPolicy:
    policy_name: str = "ntpe.controlled_runtime_execution_authorization"
    policy_version: str = "1.0"
    maximum_authorized_units: int = 1
    provider_request_limit: int = 1
    translation_request_limit: int = 1
    retry_limit: int = 0
    fallback_limit: int = 0
    output_replacement_authorized: bool = False
    production_integration_authorized: bool = False
    runtime_execution_enabled: bool = False
    provider_execution_enabled: bool = False
    network_execution_enabled: bool = False
    translation_execution_enabled: bool = False
    authorization_reusable: bool = False


DEFAULT_POLICY = ControlledRuntimeExecutionAuthorizationPolicy()

FINDING_CODES = (
    "AUTHORIZATION_RECORDED_NOT_EXECUTED",
    "EXACT_EXECUTION_PLAN_BOUND",
    "EXACT_ADAPTER_INDEX_BOUND",
    "ONE_TIME_NON_REUSABLE_AUTHORIZATION",
    "FREEZE_METADATA_MISSING",
    "FREEZE_METADATA_TYPE_INVALID",
    "FREEZE_VALIDATION_FAILED",
    "FREEZE_METADATA_MISMATCH",
    "FREEZE_GATE_MISMATCH",
    "EXECUTION_PLAN_TYPE_INVALID",
    "EXECUTION_PLAN_SCHEMA_MISMATCH",
    "EXECUTION_PLAN_STATE_INVALID",
    "EXECUTION_PLAN_SCOPE_INVALID",
    "EXECUTION_PLAN_SELECTION_AUTOMATIC",
    "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
    "EXECUTION_STEP_FINGERPRINT_MISMATCH",
    "EXECUTION_PLAN_TEXT_FINGERPRINT_MISMATCH",
    "EXECUTION_PLAN_CAPABILITY_RELAXATION",
    "EXECUTION_PLAN_ALREADY_STARTED",
    "EXECUTION_PLAN_ALREADY_COMPLETED",
    "PROVIDER_EXECUTION_COUNTER_NONZERO",
    "TRANSLATION_EXECUTION_COUNTER_NONZERO",
    "REQUEST_SCHEMA_MISMATCH",
    "REQUEST_FINGERPRINT_MISMATCH",
    "AUTHORIZATION_ID_INVALID",
    "CALLER_CONFIRMATION_REQUIRED",
    "AUTHORIZATION_SCOPE_MISMATCH",
    "PURPOSE_INVALID",
    "ADAPTER_INDEX_MISMATCH",
    "MULTIPLE_UNIT_AUTHORIZATION_REJECTED",
    "PLAN_ORDER_CHANGE_REJECTED",
    "PROVIDER_REQUEST_LIMIT_INVALID",
    "TRANSLATION_REQUEST_LIMIT_INVALID",
    "RETRY_REQUEST_REJECTED",
    "FALLBACK_REQUEST_REJECTED",
    "OUTPUT_REPLACEMENT_REQUEST_REJECTED",
    "CACHE_WRITE_REQUEST_REJECTED",
    "RESUME_WRITE_REQUEST_REJECTED",
    "PRODUCTION_INTEGRATION_REQUEST_REJECTED",
    "RUNTIME_EXECUTION_INTENT_REQUIRED",
    "PROVIDER_EXECUTION_INTENT_REQUIRED",
    "NETWORK_EXECUTION_INTENT_REQUIRED",
    "TRANSLATION_EXECUTION_INTENT_REQUIRED",
    "REQUEST_FIELD_TYPE_INVALID",
)

_INFO_CODES = {
    "AUTHORIZATION_RECORDED_NOT_EXECUTED",
    "EXACT_EXECUTION_PLAN_BOUND",
    "EXACT_ADAPTER_INDEX_BOUND",
    "ONE_TIME_NON_REUSABLE_AUTHORIZATION",
}
_FROZEN_CODES = {
    "FREEZE_METADATA_MISSING",
    "FREEZE_METADATA_TYPE_INVALID",
    "FREEZE_VALIDATION_FAILED",
    "FREEZE_METADATA_MISMATCH",
    "FREEZE_GATE_MISMATCH",
    "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
}
FINDING_SEVERITIES = MappingProxyType(
    {
        code: "info" if code in _INFO_CODES else "blocking"
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "AUTHORIZATION_RECORDED_NOT_EXECUTED": "Authorization was recorded without execution.",
        "EXACT_EXECUTION_PLAN_BOUND": "Authorization is bound to the exact frozen execution plan.",
        "EXACT_ADAPTER_INDEX_BOUND": "Authorization is bound to the plan's single explicit adapter index.",
        "ONE_TIME_NON_REUSABLE_AUTHORIZATION": "Authorization is intended for one future execution and is not reusable.",
        "FREEZE_METADATA_MISSING": "Stage 5.4 freeze metadata is required.",
        "FREEZE_METADATA_TYPE_INVALID": "Stage 5.4 freeze metadata has an invalid type.",
        "FREEZE_VALIDATION_FAILED": "The Stage 5.4 frozen preparation contract did not validate.",
        "FREEZE_METADATA_MISMATCH": "Supplied Stage 5.4 freeze metadata is not canonical.",
        "FREEZE_GATE_MISMATCH": "The Stage 5.4 activation gate is invalid.",
        "EXECUTION_PLAN_TYPE_INVALID": "The supplied execution plan has an invalid type.",
        "EXECUTION_PLAN_SCHEMA_MISMATCH": "The execution plan schema contract is invalid.",
        "EXECUTION_PLAN_STATE_INVALID": "The execution plan is not in its frozen planned state.",
        "EXECUTION_PLAN_SCOPE_INVALID": "The execution plan must contain exactly one selected unit.",
        "EXECUTION_PLAN_SELECTION_AUTOMATIC": "The execution plan does not contain one explicit adapter selection.",
        "EXECUTION_PLAN_FINGERPRINT_MISMATCH": "The execution plan fingerprint is not canonical.",
        "EXECUTION_STEP_FINGERPRINT_MISMATCH": "The selected execution step fingerprint is not canonical.",
        "EXECUTION_PLAN_TEXT_FINGERPRINT_MISMATCH": "The selected execution step text does not match its frozen source fingerprint.",
        "EXECUTION_PLAN_CAPABILITY_RELAXATION": "The execution plan attempts to relax a frozen capability boundary.",
        "EXECUTION_PLAN_ALREADY_STARTED": "The execution plan has already started.",
        "EXECUTION_PLAN_ALREADY_COMPLETED": "The execution plan has already completed.",
        "PROVIDER_EXECUTION_COUNTER_NONZERO": "The provider execution counter must remain zero.",
        "TRANSLATION_EXECUTION_COUNTER_NONZERO": "The translation execution counter must remain zero.",
        "REQUEST_SCHEMA_MISMATCH": "The authorization request schema contract is invalid.",
        "REQUEST_FINGERPRINT_MISMATCH": "The authorization request fingerprint is not canonical.",
        "AUTHORIZATION_ID_INVALID": "The authorization ID must be an explicit structurally valid caller reference.",
        "CALLER_CONFIRMATION_REQUIRED": "Explicit caller confirmation is required.",
        "AUTHORIZATION_SCOPE_MISMATCH": "Authorization scope must exactly bind the supplied plan and adapter index.",
        "PURPOSE_INVALID": "Purpose must be deterministic non-empty caller metadata.",
        "ADAPTER_INDEX_MISMATCH": "The requested adapter index does not match the execution plan.",
        "MULTIPLE_UNIT_AUTHORIZATION_REJECTED": "Only the execution plan's single selected unit may be authorized.",
        "PLAN_ORDER_CHANGE_REJECTED": "The request may not change execution plan ordering.",
        "PROVIDER_REQUEST_LIMIT_INVALID": "The provider request limit must be exactly one.",
        "TRANSLATION_REQUEST_LIMIT_INVALID": "The translation request limit must be exactly one.",
        "RETRY_REQUEST_REJECTED": "Retry authorization is prohibited.",
        "FALLBACK_REQUEST_REJECTED": "Fallback authorization is prohibited.",
        "OUTPUT_REPLACEMENT_REQUEST_REJECTED": "Output replacement authorization is prohibited.",
        "CACHE_WRITE_REQUEST_REJECTED": "Cache writes cannot be authorized.",
        "RESUME_WRITE_REQUEST_REJECTED": "Resume writes cannot be authorized.",
        "PRODUCTION_INTEGRATION_REQUEST_REJECTED": "Production integration cannot be authorized.",
        "RUNTIME_EXECUTION_INTENT_REQUIRED": "Runtime execution intent must be explicit.",
        "PROVIDER_EXECUTION_INTENT_REQUIRED": "Provider execution intent must be explicit.",
        "NETWORK_EXECUTION_INTENT_REQUIRED": "Network execution intent must be explicit.",
        "TRANSLATION_EXECUTION_INTENT_REQUIRED": "Translation execution intent must be explicit.",
        "REQUEST_FIELD_TYPE_INVALID": "Authorization request fields must use exact immutable scalar and tuple types.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)
FROZEN_FAILURE_CODES = frozenset(_FROZEN_CODES)


def exact_authorization_scope(plan_fingerprint: str, adapter_index: int) -> str:
    return (
        "controlled_runtime_execution_plan:"
        f"{plan_fingerprint}:adapter_index:{adapter_index}:unit_count:1"
    )

