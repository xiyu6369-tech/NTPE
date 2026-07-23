from __future__ import annotations

from types import MappingProxyType

from .models import ControlledRuntimeExecutionPolicy


SCHEMA_NAME = "ntpe.controlled_runtime_execution_plan"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_single_unit_execution_plan_v1"
ACTIVATION_GATE = "controlled_runtime_execution_plan_prepared"
CONSUMED_ACTIVATION_GATE = "controlled_runtime_adapter_prepared"

POLICY_NAME = "ntpe.controlled_runtime_execution_plan"
POLICY_VERSION = "1.0"
EXECUTION_MODE = "single_pass_sequential_controlled"

STEP_STATUS = "planned_not_executed"
PLAN_STATUS = "planned"
PLAN_WARNING_STATUS = "planned_with_warnings"
MANUAL_REVIEW_STATUS = "manual_review"
BLOCKED_STATUS = "blocked"
HOLD_ACTION = "hold_for_explicit_runtime_execution_enablement"
MANUAL_REVIEW_ACTION = "manual_review"
REJECT_ACTION = "reject"

DEFAULT_POLICY = ControlledRuntimeExecutionPolicy(
    policy_name=POLICY_NAME,
    policy_version=POLICY_VERSION,
    execution_mode=EXECUTION_MODE,
    maximum_units_per_execution=1,
    maximum_provider_requests_per_unit=1,
    maximum_total_provider_requests=1,
    allow_partial_scope=True,
    allow_full_package_scope=False,
    allow_parallel_execution=False,
    allow_automatic_retry=False,
    allow_automatic_fallback=False,
    allow_output_replacement=False,
    allow_output_write=False,
    allow_resume_write=False,
    allow_cache_write=False,
    allow_production_hook=False,
    runtime_execution_enabled=False,
    provider_execution_enabled=False,
    translation_execution_enabled=False,
)

PROHIBITED_TRUE_FIELDS = (
    "allow_full_package_scope",
    "allow_parallel_execution",
    "allow_automatic_retry",
    "allow_automatic_fallback",
    "allow_output_replacement",
    "allow_output_write",
    "allow_resume_write",
    "allow_cache_write",
    "allow_production_hook",
    "runtime_execution_enabled",
    "provider_execution_enabled",
    "translation_execution_enabled",
)

FINDING_CODES = (
    "CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED",
    "SINGLE_UNIT_EXECUTION_SCOPE",
    "ADAPTER_WARNING_PROPAGATED",
    "EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED",
    "RUNTIME_EXECUTION_NOT_STARTED",
    "RUNTIME_EXECUTION_NOT_COMPLETED",
    "PROVIDER_REQUEST_COUNT_ZERO",
    "TRANSLATION_EXECUTION_COUNT_ZERO",
    "ADAPTER_PREPARATION_INVALID",
    "ADAPTER_REQUEST_SCHEMA_MISMATCH",
    "ADAPTER_REQUEST_GATE_MISMATCH",
    "ADAPTER_REQUEST_FINGERPRINT_MISMATCH",
    "ADAPTER_PREPARATION_FINGERPRINT_MISMATCH",
    "ADAPTER_CAPABILITY_PROFILE_MISMATCH",
    "EXECUTION_SCOPE_EMPTY",
    "EXECUTION_SCOPE_MULTIPLE_UNITS_REJECTED",
    "EXECUTION_SCOPE_TYPE_MISMATCH",
    "EXECUTION_SCOPE_OUT_OF_RANGE",
    "EXECUTION_SCOPE_NOT_APPROVED",
    "ADAPTER_UNIT_NOT_FOUND",
    "ADAPTER_UNIT_STATE_INVALID",
    "ADAPTER_UNIT_FINGERPRINT_MISMATCH",
    "ADAPTER_UNIT_TEXT_MISMATCH",
    "ADAPTER_UNIT_OFFSET_INVALID",
    "PROVIDER_REQUEST_LIMIT_EXCEEDED",
    "RETRY_NOT_AUTHORIZED",
    "FALLBACK_NOT_AUTHORIZED",
    "OUTPUT_REPLACEMENT_NOT_AUTHORIZED",
    "RUNTIME_EXECUTION_CAPABILITY_DISABLED",
    "PROVIDER_EXECUTION_CAPABILITY_DISABLED",
    "TRANSLATION_EXECUTION_CAPABILITY_DISABLED",
)

_INFO_CODES = {
    "CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED",
    "SINGLE_UNIT_EXECUTION_SCOPE",
    "EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED",
    "RUNTIME_EXECUTION_NOT_STARTED",
    "RUNTIME_EXECUTION_NOT_COMPLETED",
    "PROVIDER_REQUEST_COUNT_ZERO",
    "TRANSLATION_EXECUTION_COUNT_ZERO",
    "RUNTIME_EXECUTION_CAPABILITY_DISABLED",
    "PROVIDER_EXECUTION_CAPABILITY_DISABLED",
    "TRANSLATION_EXECUTION_CAPABILITY_DISABLED",
}
FINDING_SEVERITIES = MappingProxyType(
    {
        code: (
            "info"
            if code in _INFO_CODES
            else "warning"
            if code == "ADAPTER_WARNING_PROPAGATED"
            else "blocking"
        )
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "CONTROLLED_RUNTIME_EXECUTION_PLAN_PREPARED": "A single-unit controlled runtime execution plan was prepared.",
        "SINGLE_UNIT_EXECUTION_SCOPE": "Exactly one caller-selected adapter unit is planned.",
        "ADAPTER_WARNING_PROPAGATED": "Warnings from the adapter preparation remain visible.",
        "EXPLICIT_RUNTIME_ENABLEMENT_REQUIRED": "Explicit runtime execution enablement remains required.",
        "RUNTIME_EXECUTION_NOT_STARTED": "Runtime execution has not started.",
        "RUNTIME_EXECUTION_NOT_COMPLETED": "Runtime execution has not completed.",
        "PROVIDER_REQUEST_COUNT_ZERO": "No provider request was executed.",
        "TRANSLATION_EXECUTION_COUNT_ZERO": "No translation execution was completed.",
        "ADAPTER_PREPARATION_INVALID": "The adapter preparation result is not eligible for planning.",
        "ADAPTER_REQUEST_SCHEMA_MISMATCH": "The adapter request schema contract is invalid.",
        "ADAPTER_REQUEST_GATE_MISMATCH": "The adapter request activation gate or state is invalid.",
        "ADAPTER_REQUEST_FINGERPRINT_MISMATCH": "The adapter request fingerprint is not canonical.",
        "ADAPTER_PREPARATION_FINGERPRINT_MISMATCH": "The adapter preparation fingerprint is not canonical.",
        "ADAPTER_CAPABILITY_PROFILE_MISMATCH": "The adapter capability profile is invalid or inconsistent.",
        "EXECUTION_SCOPE_EMPTY": "The caller must explicitly select one adapter unit.",
        "EXECUTION_SCOPE_MULTIPLE_UNITS_REJECTED": "This stage cannot plan more than one adapter unit.",
        "EXECUTION_SCOPE_TYPE_MISMATCH": "The selected adapter unit index must be an integer and not a boolean.",
        "EXECUTION_SCOPE_OUT_OF_RANGE": "The selected adapter unit index is outside the request range.",
        "EXECUTION_SCOPE_NOT_APPROVED": "The selected adapter unit is not in the approved upstream scope.",
        "ADAPTER_UNIT_NOT_FOUND": "The selected adapter unit does not exist.",
        "ADAPTER_UNIT_STATE_INVALID": "The adapter unit is not in its initial prepared state.",
        "ADAPTER_UNIT_FINGERPRINT_MISMATCH": "An adapter unit fingerprint is not canonical.",
        "ADAPTER_UNIT_TEXT_MISMATCH": "Adapter unit text or character metadata is inconsistent.",
        "ADAPTER_UNIT_OFFSET_INVALID": "An adapter unit has invalid source offsets.",
        "PROVIDER_REQUEST_LIMIT_EXCEEDED": "The policy cannot plan the required single provider request.",
        "RETRY_NOT_AUTHORIZED": "Retry is not authorized by the execution plan.",
        "FALLBACK_NOT_AUTHORIZED": "Fallback is not authorized by the execution plan.",
        "OUTPUT_REPLACEMENT_NOT_AUTHORIZED": "Output replacement is not authorized by the execution plan.",
        "RUNTIME_EXECUTION_CAPABILITY_DISABLED": "Runtime execution capability remains disabled.",
        "PROVIDER_EXECUTION_CAPABILITY_DISABLED": "Provider execution capability remains disabled.",
        "TRANSLATION_EXECUTION_CAPABILITY_DISABLED": "Translation execution capability remains disabled.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)
