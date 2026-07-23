from __future__ import annotations

from types import MappingProxyType

from .models import RuntimeAdapterCapabilityProfile


SCHEMA_NAME = "ntpe.controlled_runtime_adapter_request"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_offline_runtime_adapter_v1"
ACTIVATION_GATE = "controlled_runtime_adapter_prepared"
CONSUMED_ACTIVATION_GATE = "controlled_runtime_submission_prepared"

PROFILE_NAME = "ntpe.controlled_runtime_adapter.offline_preparation"
PROFILE_VERSION = "1.0"

UNIT_STATUS = "prepared_for_runtime_adapter"
PACKAGE_STATUS = "prepared_for_runtime_adapter"
PACKAGE_WARNING_STATUS = "prepared_for_runtime_adapter_with_warnings"
BLOCKED_STATUS = "blocked"
HOLD_ACTION = "hold_for_controlled_runtime_execution_stage"
MANUAL_REVIEW_ACTION = "manual_review"
REJECT_ACTION = "reject"
STATUS_ACTIONS = MappingProxyType(
    {
        PACKAGE_STATUS: HOLD_ACTION,
        PACKAGE_WARNING_STATUS: HOLD_ACTION,
        BLOCKED_STATUS: REJECT_ACTION,
    }
)

PROHIBITED_CAPABILITIES = (
    "supports_provider_execution",
    "supports_translation_execution",
    "supports_automatic_retry",
    "supports_automatic_fallback",
    "supports_output_replacement",
    "supports_resume_write",
    "supports_cache_write",
    "supports_output_write",
    "supports_production_hook",
)

DEFAULT_CAPABILITY_PROFILE = RuntimeAdapterCapabilityProfile(
    profile_name=PROFILE_NAME,
    profile_version=PROFILE_VERSION,
    supports_controlled_submission=True,
    supports_partial_scope=True,
    supports_full_package_scope=True,
    supports_provider_execution=False,
    supports_translation_execution=False,
    supports_automatic_retry=False,
    supports_automatic_fallback=False,
    supports_output_replacement=False,
    supports_resume_write=False,
    supports_cache_write=False,
    supports_output_write=False,
    supports_production_hook=False,
)

FINDING_CODES = (
    "RUNTIME_ADAPTER_REQUEST_PREPARED",
    "RUNTIME_EXECUTION_NOT_PERFORMED",
    "PROVIDER_EXECUTION_NOT_PERFORMED",
    "TRANSLATION_EXECUTION_NOT_PERFORMED",
    "SUBMISSION_WARNING_PROPAGATED",
    "PARTIAL_SCOPE_ADAPTER_REQUEST",
    "FULL_PACKAGE_ADAPTER_REQUEST",
    "SUBMISSION_SCHEMA_MISMATCH",
    "SUBMISSION_VERSION_MISMATCH",
    "SUBMISSION_STRATEGY_MISMATCH",
    "SUBMISSION_GATE_MISMATCH",
    "SUBMISSION_FINGERPRINT_MISMATCH",
    "SUBMISSION_SCOPE_MISMATCH",
    "SUBMISSION_UNIT_COUNT_MISMATCH",
    "SUBMISSION_UNIT_ORDER_MISMATCH",
    "SUBMISSION_UNIT_TEXT_MISMATCH",
    "SUBMISSION_UNIT_OFFSET_INVALID",
    "SUBMISSION_UNIT_FINGERPRINT_MISMATCH",
    "SUBMISSION_ALREADY_EXECUTED",
    "PROVIDER_REQUEST_ALREADY_DETECTED",
    "TRANSLATION_RESULT_ALREADY_DETECTED",
    "CAPABILITY_PROFILE_MISMATCH",
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

_INFO_CODES = {
    "RUNTIME_ADAPTER_REQUEST_PREPARED",
    "RUNTIME_EXECUTION_NOT_PERFORMED",
    "PROVIDER_EXECUTION_NOT_PERFORMED",
    "TRANSLATION_EXECUTION_NOT_PERFORMED",
    "FULL_PACKAGE_ADAPTER_REQUEST",
    "PROVIDER_CAPABILITY_NOT_AVAILABLE",
    "TRANSLATION_CAPABILITY_NOT_AVAILABLE",
    "AUTOMATIC_RETRY_NOT_SUPPORTED",
    "AUTOMATIC_FALLBACK_NOT_SUPPORTED",
    "OUTPUT_REPLACEMENT_NOT_SUPPORTED",
    "OUTPUT_WRITE_NOT_SUPPORTED",
    "RESUME_WRITE_NOT_SUPPORTED",
    "CACHE_WRITE_NOT_SUPPORTED",
    "PRODUCTION_HOOK_NOT_SUPPORTED",
}
FINDING_SEVERITIES = MappingProxyType(
    {
        code: (
            "info"
            if code in _INFO_CODES
            else "warning"
            if code in {"SUBMISSION_WARNING_PROPAGATED", "PARTIAL_SCOPE_ADAPTER_REQUEST"}
            else "blocking"
        )
        for code in FINDING_CODES
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "RUNTIME_ADAPTER_REQUEST_PREPARED": "The runtime adapter request was prepared offline.",
        "RUNTIME_EXECUTION_NOT_PERFORMED": "The runtime was not invoked.",
        "PROVIDER_EXECUTION_NOT_PERFORMED": "No provider was invoked.",
        "TRANSLATION_EXECUTION_NOT_PERFORMED": "No translation was executed.",
        "SUBMISSION_WARNING_PROPAGATED": "Submission warnings remain visible in the adapter contract.",
        "PARTIAL_SCOPE_ADAPTER_REQUEST": "The adapter request preserves an explicitly approved partial scope.",
        "FULL_PACKAGE_ADAPTER_REQUEST": "The adapter request covers the complete execution package scope.",
        "SUBMISSION_SCHEMA_MISMATCH": "The submission schema name is invalid.",
        "SUBMISSION_VERSION_MISMATCH": "The submission schema version is invalid.",
        "SUBMISSION_STRATEGY_MISMATCH": "The submission strategy is invalid.",
        "SUBMISSION_GATE_MISMATCH": "The submission activation gate is invalid.",
        "SUBMISSION_FINGERPRINT_MISMATCH": "The submission package fingerprint is not canonical.",
        "SUBMISSION_SCOPE_MISMATCH": "Submission scope and coverage metadata are inconsistent.",
        "SUBMISSION_UNIT_COUNT_MISMATCH": "Submission unit cardinality is inconsistent.",
        "SUBMISSION_UNIT_ORDER_MISMATCH": "Submission units are not in approved canonical order.",
        "SUBMISSION_UNIT_TEXT_MISMATCH": "Submission unit text or character metadata is inconsistent.",
        "SUBMISSION_UNIT_OFFSET_INVALID": "A submission unit has invalid source offsets.",
        "SUBMISSION_UNIT_FINGERPRINT_MISMATCH": "A submission unit fingerprint is not canonical.",
        "SUBMISSION_ALREADY_EXECUTED": "The submission package was already executed.",
        "PROVIDER_REQUEST_ALREADY_DETECTED": "The submission records a provider request.",
        "TRANSLATION_RESULT_ALREADY_DETECTED": "The submission records a completed translation.",
        "CAPABILITY_PROFILE_MISMATCH": "The capability profile is incompatible or relaxes the offline boundary.",
        "PROVIDER_CAPABILITY_NOT_AVAILABLE": "Provider execution capability is intentionally unavailable.",
        "TRANSLATION_CAPABILITY_NOT_AVAILABLE": "Translation execution capability is intentionally unavailable.",
        "AUTOMATIC_RETRY_NOT_SUPPORTED": "Automatic retry is not supported.",
        "AUTOMATIC_FALLBACK_NOT_SUPPORTED": "Automatic fallback is not supported.",
        "OUTPUT_REPLACEMENT_NOT_SUPPORTED": "Output replacement is not supported.",
        "OUTPUT_WRITE_NOT_SUPPORTED": "Output writes are not supported.",
        "RESUME_WRITE_NOT_SUPPORTED": "Resume writes are not supported.",
        "CACHE_WRITE_NOT_SUPPORTED": "Cache writes are not supported.",
        "PRODUCTION_HOOK_NOT_SUPPORTED": "Production hooks are not supported.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)
