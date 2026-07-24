"""Stage 6.4 — Controlled Runtime Execution Envelope Policy

Immutable policy constants governing execution envelope preparation.
Does NOT execute, does NOT write, does NOT contact providers or network.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Successful state constants
# ---------------------------------------------------------------------------

SUCCESS_STATUS = "runtime_handoff_prepared_not_executed"
SUCCESS_ACTION = "retain_for_controlled_runtime_handoff"

# ---------------------------------------------------------------------------
# Allowed / disallowed statuses
# ---------------------------------------------------------------------------

ALLOWED_RESULT_STATUSES: tuple[str, ...] = (
    "runtime_handoff_prepared_not_executed",
    "rejected",
    "invalid_request",
    "upstream_contract_mismatch",
    "authorization_not_consumed",
    "durable_claim_mismatch",
    "execution_scope_mismatch",
    "execution_unit_mismatch",
    "runtime_handoff_not_eligible",
    "verification_failed",
)

ALLOWED_RECOMMENDED_ACTIONS: tuple[str, ...] = (
    "retain_for_controlled_runtime_handoff",
    "correct_request",
    "rebuild_from_frozen_contract",
    "reject",
    "manual_integrity_review",
    "do_not_execute",
)

ALLOWED_ENVELOPE_STATES: tuple[str, ...] = (
    "runtime_handoff_prepared_not_executed",
)

ALLOWED_EXECUTION_MODES: tuple[str, ...] = (
    "controlled_single_execution",
)

# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

SEVERITY_LEVELS: tuple[str, ...] = ("info", "warning", "error", "blocking")

# ---------------------------------------------------------------------------
# Frozen gate constants (Stage 5.4)
# ---------------------------------------------------------------------------

FROZEN_ACTIVATION_GATE = "controlled_runtime_preparation_frozen"
FROZEN_COMPONENT = "controlled_runtime_preparation"
FROZEN_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Stage 5.3 plan constants
# ---------------------------------------------------------------------------

PLAN_SCHEMA_NAME = "ntpe.controlled_runtime_execution_plan"
PLAN_SCHEMA_VERSION = "1.0"
PLAN_STRATEGY = "controlled_single_unit"
PLAN_ACTIVATION_GATE = "controlled_runtime_execution_plan_prepared"
PLAN_STATUSES: frozenset[str] = frozenset(
    {"planned_not_executed", "planned_with_warnings"}
)
PLAN_ACTION = "retain_for_controlled_runtime_auth_request"
STEP_STATUS = "planned_not_executed"

# ---------------------------------------------------------------------------
# Stage 6.1 authorization constants
# ---------------------------------------------------------------------------

AUTH_REQUEST_SCHEMA_NAME = (
    "ntpe.controlled_runtime_execution_authorization_request"
)
AUTH_REQUEST_SCHEMA_VERSION = "1.0"
AUTH_DECISION_SCHEMA_NAME = (
    "ntpe.controlled_runtime_execution_authorization_decision"
)
AUTH_DECISION_SCHEMA_VERSION = "1.0"
AUTHORIZED_STATUS = "authorized_not_executed"

# ---------------------------------------------------------------------------
# Stage 6.2 consumption constants
# ---------------------------------------------------------------------------

STAGE62_REQUEST_SCHEMA_NAME = (
    "ntpe.controlled_runtime_authorization_consumption_request"
)
STAGE62_REQUEST_SCHEMA_VERSION = "1.0"
STAGE62_RECORD_SCHEMA_NAME = (
    "ntpe.controlled_runtime_authorization_consumption_record"
)
STAGE62_RECORD_SCHEMA_VERSION = "1.0"
STAGE62_PREPARED_STATUS = "consumption_prepared_not_executed"

# ---------------------------------------------------------------------------
# Stage 6.3 claim constants
# ---------------------------------------------------------------------------

STAGE63_REQUEST_SCHEMA_NAME = (
    "ntpe.controlled_runtime_atomic_authorization_consumption_claim_request"
)
STAGE63_REQUEST_SCHEMA_VERSION = "1.0"
STAGE63_CLAIM_SCHEMA_NAME = (
    "ntpe.controlled_runtime_atomic_authorization_consumption_claim"
)
STAGE63_CLAIM_SCHEMA_VERSION = "1.0"
STAGE63_CLAIM_STATE = "durably_consumed_not_executed"
STAGE63_RESULT_STATUS = "durably_consumed_not_executed"

# ---------------------------------------------------------------------------
# Finding codes and mappings
# ---------------------------------------------------------------------------

FINDING_CODES: tuple[str, ...] = (
    # Request-level
    "REQUEST_SCHEMA_MISMATCH",
    "REQUEST_VERSION_MISMATCH",
    "REQUEST_FINGERPRINT_MISMATCH",
    "ENVELOPE_ID_MISSING",
    "ENVELOPE_ID_BLANK",
    "ENVELOPE_ID_INVALID",
    "CALLER_CONFIRMATION_MISSING",
    "CALLER_CONFIRMATION_FALSE",
    "CALLER_CONFIRMATION_TYPE_INVALID",
    "RUNTIME_HANDOFF_REQUESTED_FALSE",
    "RUNTIME_HANDOFF_REQUESTED_TYPE_INVALID",
    "UNIT_COUNT_ZERO",
    "UNIT_COUNT_GREATER_THAN_ONE",
    "UNIT_COUNT_TYPE_INVALID",
    "EXECUTION_MODE_INVALID",
    "RUNTIME_SCOPE_INVALID",
    "CLAIM_ID_MISMATCH",
    "CONSUMPTION_ID_MISMATCH",
    "AUTHORIZATION_ID_MISMATCH",
    "AUTH_REQUEST_FINGERPRINT_MISMATCH",
    "AUTH_DECISION_FINGERPRINT_MISMATCH",
    "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
    "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
    "STAGE62_RECORD_FINGERPRINT_MISMATCH",
    "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH",
    "STAGE63_CLAIM_FINGERPRINT_MISMATCH",
    "ADAPTER_INDEX_MISMATCH",
    "PURPOSE_INVALID",
    # Freeze
    "FREEZE_GATE_INVALID",
    "FREEZE_VALIDATION_FAILED",
    # Plan
    "PLAN_SCHEMA_MISMATCH",
    "PLAN_STATE_INVALID",
    "PLAN_SCOPE_INVALID",
    "PLAN_ALREADY_STARTED",
    "PLAN_ALREADY_COMPLETED",
    "PLAN_NONZERO_COUNTERS",
    "PLAN_FINGERPRINT_MISMATCH",
    # Stage 6.1
    "AUTHORIZATION_NOT_AUTHORIZED",
    "AUTHORIZATION_REUSABLE",
    "AUTHORIZATION_ALREADY_EXECUTED",
    "AUTHORIZATION_REQUEST_INVALID",
    "AUTHORIZATION_DECISION_INVALID",
    # Stage 6.2
    "STAGE62_REQUEST_INVALID",
    "STAGE62_RECORD_INVALID",
    "STAGE62_RESULT_INVALID",
    "STAGE62_NOT_PREPARED",
    "STAGE62_ALREADY_CONSUMED",
    "STAGE62_FALSE_DURABLE_CLAIM",
    "STAGE62_FALSE_REGISTRY_CLAIM",
    # Stage 6.3
    "STAGE63_CLAIM_REQUEST_INVALID",
    "STAGE63_CLAIM_INVALID",
    "STAGE63_RESULT_INVALID",
    "STAGE63_AUTHORIZATION_NOT_CONSUMED",
    "STAGE63_AUTHORIZATION_REUSABLE",
    "STAGE63_DURABLE_PREVENTION_FALSE",
    "STAGE63_REGISTRY_WRITTEN_FALSE",
    "STAGE63_DUPLICATE_CLAIM_DETECTED",
    "STAGE63_EXECUTION_STARTED",
    "STAGE63_EXECUTION_COMPLETED",
    "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED",
    # Capabilities
    "RUNTIME_EXECUTION_ENABLED",
    "PROVIDER_EXECUTION_ENABLED",
    "NETWORK_EXECUTION_ENABLED",
    "TRANSLATION_EXECUTION_ENABLED",
    "OUTPUT_WRITE_ENABLED",
    "RESUME_WRITE_ENABLED",
    "CACHE_WRITE_ENABLED",
    "RETRY_ENABLED",
    "FALLBACK_ENABLED",
    "PRODUCTION_HOOK_ENABLED",
    "RUNTIME_HANDOFF_ALREADY_COMPLETED",
    # Chain
    "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH",
    "UPSTREAM_FINGERPRINT_CHAIN_ALTERED",
)

_BLOCKING_CODES: frozenset[str] = frozenset(
    {
        "REQUEST_FINGERPRINT_MISMATCH",
        "ENVELOPE_ID_MISSING",
        "ENVELOPE_ID_BLANK",
        "ENVELOPE_ID_INVALID",
        "CALLER_CONFIRMATION_MISSING",
        "CALLER_CONFIRMATION_FALSE",
        "EXECUTION_MODE_INVALID",
        "UNIT_COUNT_ZERO",
        "UNIT_COUNT_GREATER_THAN_ONE",
        "UNIT_COUNT_TYPE_INVALID",
        "RUNTIME_SCOPE_INVALID",
        "FREEZE_GATE_INVALID",
        "PLAN_STATE_INVALID",
        "PLAN_ALREADY_STARTED",
        "PLAN_ALREADY_COMPLETED",
        "AUTHORIZATION_NOT_AUTHORIZED",
        "AUTHORIZATION_REUSABLE",
        "AUTHORIZATION_ALREADY_EXECUTED",
        "STAGE62_ALREADY_CONSUMED",
        "STAGE62_NOT_PREPARED",
        "STAGE63_AUTHORIZATION_NOT_CONSUMED",
        "STAGE63_AUTHORIZATION_REUSABLE",
        "STAGE63_DURABLE_PREVENTION_FALSE",
        "STAGE63_REGISTRY_WRITTEN_FALSE",
        "STAGE63_DUPLICATE_CLAIM_DETECTED",
        "STAGE63_EXECUTION_STARTED",
        "STAGE63_EXECUTION_COMPLETED",
        "RUNTIME_EXECUTION_ENABLED",
        "PROVIDER_EXECUTION_ENABLED",
        "NETWORK_EXECUTION_ENABLED",
        "TRANSLATION_EXECUTION_ENABLED",
        "OUTPUT_WRITE_ENABLED",
        "RESUME_WRITE_ENABLED",
        "CACHE_WRITE_ENABLED",
        "RETRY_ENABLED",
        "FALLBACK_ENABLED",
        "PRODUCTION_HOOK_ENABLED",
        "RUNTIME_HANDOFF_REQUESTED_FALSE",
        "RUNTIME_HANDOFF_ALREADY_COMPLETED",
        "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH",
        "UPSTREAM_FINGERPRINT_CHAIN_ALTERED",
        "CLAIM_ID_MISMATCH",
        "CONSUMPTION_ID_MISMATCH",
        "AUTHORIZATION_ID_MISMATCH",
        "AUTH_REQUEST_FINGERPRINT_MISMATCH",
        "AUTH_DECISION_FINGERPRINT_MISMATCH",
        "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
        "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
        "STAGE62_RECORD_FINGERPRINT_MISMATCH",
        "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH",
        "STAGE63_CLAIM_FINGERPRINT_MISMATCH",
        "ADAPTER_INDEX_MISMATCH",
        "PLAN_FINGERPRINT_MISMATCH",
        "PLAN_SCOPE_INVALID",
        "PLAN_NONZERO_COUNTERS",
        "STAGE62_FALSE_DURABLE_CLAIM",
        "STAGE62_FALSE_REGISTRY_CLAIM",
        "STAGE63_CLAIM_INVALID",
        "STAGE63_CLAIM_REQUEST_INVALID",
        "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED",
        "REQUEST_SCHEMA_MISMATCH",
    }
)

_ERROR_CODES: frozenset[str] = frozenset(
    {
        "REQUEST_SCHEMA_MISMATCH",
        "REQUEST_VERSION_MISMATCH",
        "CALLER_CONFIRMATION_TYPE_INVALID",
        "RUNTIME_HANDOFF_REQUESTED_TYPE_INVALID",
        "RUNTIME_SCOPE_INVALID",
        "CLAIM_ID_MISMATCH",
        "CONSUMPTION_ID_MISMATCH",
        "AUTHORIZATION_ID_MISMATCH",
        "AUTH_REQUEST_FINGERPRINT_MISMATCH",
        "AUTH_DECISION_FINGERPRINT_MISMATCH",
        "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
        "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
        "STAGE62_RECORD_FINGERPRINT_MISMATCH",
        "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH",
        "STAGE63_CLAIM_FINGERPRINT_MISMATCH",
        "ADAPTER_INDEX_MISMATCH",
        "PURPOSE_INVALID",
        "FREEZE_VALIDATION_FAILED",
        "PLAN_SCHEMA_MISMATCH",
        "PLAN_SCOPE_INVALID",
        "PLAN_NONZERO_COUNTERS",
        "PLAN_FINGERPRINT_MISMATCH",
        "AUTHORIZATION_REQUEST_INVALID",
        "AUTHORIZATION_DECISION_INVALID",
        "STAGE62_REQUEST_INVALID",
        "STAGE62_RECORD_INVALID",
        "STAGE62_RESULT_INVALID",
        "STAGE62_FALSE_DURABLE_CLAIM",
        "STAGE62_FALSE_REGISTRY_CLAIM",
        "STAGE63_CLAIM_REQUEST_INVALID",
        "STAGE63_CLAIM_INVALID",
        "STAGE63_RESULT_INVALID",
        "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED",
        "UPSTREAM_FINGERPRINT_CHAIN_ALTERED",
    }
)

FINDING_SEVERITIES: dict[str, str] = {
    code: (
        "blocking"
        if code in _BLOCKING_CODES
        else "error"
        if code in _ERROR_CODES
        else "warning"
    )
    for code in FINDING_CODES
}

FINDING_MESSAGES: dict[str, str] = {
    "REQUEST_SCHEMA_MISMATCH": "Envelope request uses wrong schema.",
    "REQUEST_VERSION_MISMATCH": "Envelope request uses unsupported schema version.",
    "REQUEST_FINGERPRINT_MISMATCH": "Request fingerprint does not match canonical payload.",
    "ENVELOPE_ID_MISSING": "envelope_id is None or absent.",
    "ENVELOPE_ID_BLANK": "envelope_id is blank.",
    "ENVELOPE_ID_INVALID": "envelope_id is malformed.",
    "CALLER_CONFIRMATION_MISSING": "caller_confirmation is missing.",
    "CALLER_CONFIRMATION_FALSE": "caller_confirmation must be true.",
    "CALLER_CONFIRMATION_TYPE_INVALID": "caller_confirmation must be bool.",
    "RUNTIME_HANDOFF_REQUESTED_FALSE": "runtime_handoff_requested must be true.",
    "RUNTIME_HANDOFF_REQUESTED_TYPE_INVALID": "runtime_handoff_requested must be bool.",
    "UNIT_COUNT_ZERO": "requested_unit_count must be 1, got 0.",
    "UNIT_COUNT_GREATER_THAN_ONE": "requested_unit_count must be exactly 1.",
    "UNIT_COUNT_TYPE_INVALID": "requested_unit_count must be int, not bool.",
    "EXECUTION_MODE_INVALID": "execution_mode must be controlled_single_execution.",
    "RUNTIME_SCOPE_INVALID": "runtime_scope must bind exact upstream identifiers.",
    "CLAIM_ID_MISMATCH": "claim_id does not match Stage 6.3 claim.",
    "CONSUMPTION_ID_MISMATCH": "consumption_id does not match Stage 6.2 record.",
    "AUTHORIZATION_ID_MISMATCH": "authorization_id does not match Stage 6.1 decision.",
    "AUTH_REQUEST_FINGERPRINT_MISMATCH": "authorization_request_fingerprint does not match upstream.",
    "AUTH_DECISION_FINGERPRINT_MISMATCH": "authorization_decision_fingerprint does not match upstream.",
    "EXECUTION_PLAN_FINGERPRINT_MISMATCH": "execution_plan_fingerprint does not match upstream.",
    "STAGE62_REQUEST_FINGERPRINT_MISMATCH": "stage62_request_fingerprint does not match upstream.",
    "STAGE62_RECORD_FINGERPRINT_MISMATCH": "stage62_record_fingerprint does not match upstream.",
    "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH": "stage63_claim_request_fingerprint does not match upstream.",
    "STAGE63_CLAIM_FINGERPRINT_MISMATCH": "stage63_claim_fingerprint does not match upstream.",
    "ADAPTER_INDEX_MISMATCH": "selected_adapter_index does not match upstream.",
    "PURPOSE_INVALID": "purpose must be non-empty metadata.",
    "FREEZE_GATE_INVALID": "Stage 5.4 freeze gate is not controlled_runtime_preparation_frozen.",
    "FREEZE_VALIDATION_FAILED": "Stage 5.4 freeze did not validate.",
    "PLAN_SCHEMA_MISMATCH": "Stage 5.3 plan has wrong schema.",
    "PLAN_STATE_INVALID": "Stage 5.3 plan state is not planned_not_executed.",
    "PLAN_SCOPE_INVALID": "Stage 5.3 plan scope must be exactly one unit.",
    "PLAN_ALREADY_STARTED": "Stage 5.3 plan execution_started is true.",
    "PLAN_ALREADY_COMPLETED": "Stage 5.3 plan execution_completed is true.",
    "PLAN_NONZERO_COUNTERS": "Stage 5.3 plan execution counters are nonzero.",
    "PLAN_FINGERPRINT_MISMATCH": "Plan fingerprint does not match canonical payload.",
    "AUTHORIZATION_NOT_AUTHORIZED": "Stage 6.1 authorization was not granted.",
    "AUTHORIZATION_REUSABLE": "Stage 6.1 authorization is reusable.",
    "AUTHORIZATION_ALREADY_EXECUTED": "Stage 6.1 authorization status is not authorized_not_executed.",
    "AUTHORIZATION_REQUEST_INVALID": "Stage 6.1 authorization request is invalid.",
    "AUTHORIZATION_DECISION_INVALID": "Stage 6.1 authorization decision is invalid.",
    "STAGE62_REQUEST_INVALID": "Stage 6.2 consumption request is invalid.",
    "STAGE62_RECORD_INVALID": "Stage 6.2 consumption record is invalid.",
    "STAGE62_RESULT_INVALID": "Stage 6.2 consumption result is invalid.",
    "STAGE62_NOT_PREPARED": "Stage 6.2 consumption was not prepared.",
    "STAGE62_ALREADY_CONSUMED": "Stage 6.2 authorization_consumed is true.",
    "STAGE62_FALSE_DURABLE_CLAIM": "Stage 6.2 falsely claimed durable enforcement.",
    "STAGE62_FALSE_REGISTRY_CLAIM": "Stage 6.2 falsely claimed registry write.",
    "STAGE63_CLAIM_REQUEST_INVALID": "Stage 6.3 claim request is invalid.",
    "STAGE63_CLAIM_INVALID": "Stage 6.3 claim is invalid.",
    "STAGE63_RESULT_INVALID": "Stage 6.3 result is invalid.",
    "STAGE63_AUTHORIZATION_NOT_CONSUMED": "Stage 6.3 authorization_consumed is false.",
    "STAGE63_AUTHORIZATION_REUSABLE": "Stage 6.3 authorization_reusable is true.",
    "STAGE63_DURABLE_PREVENTION_FALSE": "Stage 6.3 durable_reuse_prevention_established is false.",
    "STAGE63_REGISTRY_WRITTEN_FALSE": "Stage 6.3 persistent_registry_written is false.",
    "STAGE63_DUPLICATE_CLAIM_DETECTED": "Stage 6.3 duplicate_claim_detected is true.",
    "STAGE63_EXECUTION_STARTED": "Stage 6.3 execution_started is true.",
    "STAGE63_EXECUTION_COMPLETED": "Stage 6.3 execution_completed is true.",
    "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED": "Stage 6.3 atomic_claim_committed is false.",
    "RUNTIME_EXECUTION_ENABLED": "Runtime execution enabled must be false.",
    "PROVIDER_EXECUTION_ENABLED": "Provider execution enabled must be false.",
    "NETWORK_EXECUTION_ENABLED": "Network execution enabled must be false.",
    "TRANSLATION_EXECUTION_ENABLED": "Translation execution enabled must be false.",
    "OUTPUT_WRITE_ENABLED": "Output write enabled must be false.",
    "RESUME_WRITE_ENABLED": "Resume write enabled must be false.",
    "CACHE_WRITE_ENABLED": "Cache write enabled must be false.",
    "RETRY_ENABLED": "Retry enabled must be false.",
    "FALLBACK_ENABLED": "Fallback enabled must be false.",
    "PRODUCTION_HOOK_ENABLED": "Production hook enabled must be false.",
    "RUNTIME_HANDOFF_ALREADY_COMPLETED": "runtime_handoff_completed must be false.",
    "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH": "Upstream fingerprint chain does not match expected layers.",
    "UPSTREAM_FINGERPRINT_CHAIN_ALTERED": "Upstream fingerprint chain has been tampered with.",
}

FINDING_ORDER: dict[str, int] = {
    code: idx for idx, code in enumerate(FINDING_CODES)
}

# ---------------------------------------------------------------------------
# Stage 6.4 Policy dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeExecutionEnvelopePolicy:
    """Immutable policy for Stage 6.4 execution envelope preparation.

    Encodes exact state requirements for all upstream stages.
    Does NOT execute, does NOT write, does NOT contact providers or network.
    """

    min_upstream_chain_layers: int = 14
    complete_chain_layers: int = 15
    allowed_execution_mode: str = "controlled_single_execution"
    success_envelope_state: str = "runtime_handoff_prepared_not_executed"
    max_findings: int = 200

    # Upstream required schemas for verification
    required_upstream_schemas: tuple[str, ...] = (
        PLAN_SCHEMA_NAME,
        AUTH_REQUEST_SCHEMA_NAME,
        AUTH_DECISION_SCHEMA_NAME,
        STAGE62_REQUEST_SCHEMA_NAME,
        STAGE62_RECORD_SCHEMA_NAME,
        STAGE63_REQUEST_SCHEMA_NAME,
        STAGE63_CLAIM_SCHEMA_NAME,
    )


DEFAULT_POLICY = ControlledRuntimeExecutionEnvelopePolicy()


# ---------------------------------------------------------------------------
# Runtime scope binding helper
# ---------------------------------------------------------------------------


def exact_envelope_runtime_scope(
    *,
    authorization_id: str,
    claim_id: str,
    execution_plan_fingerprint: str,
    selected_adapter_index: int,
) -> str:
    """Produce the exact runtime scope string binding one authorization,
    one durable claim, one execution plan, and one adapter index.

    This deterministic scope can be used as `runtime_scope` in the request.
    """
    return (
        f"auth={authorization_id}"
        f" claim={claim_id}"
        f" plan={execution_plan_fingerprint}"
        f" adapter={selected_adapter_index}"
        f" unit_count=1"
    )