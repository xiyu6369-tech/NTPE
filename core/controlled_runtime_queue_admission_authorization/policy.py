"""Centralized immutable Stage 6.10 policy."""

from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_authorization_request"
REQUEST_SCHEMA_VERSION = "1.0"
DECISION_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_authorization_decision"
DECISION_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_authorization_result"
RESULT_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = (
    "ntpe.controlled_runtime_queue_admission_authorization_verification_result"
)
VERIFICATION_SCHEMA_VERSION = "1.0"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
ADMISSION_INTENT = "authorize_exactly_one_controlled_queue_admission"
AUTHORIZED_STATUS = "queue_admission_authorized_not_consumed"
DENIED_STATUS = "queue_admission_denied"

REASON_CODES = (
    "INVALID_INPUT_TYPE",
    "INVALID_SCHEMA",
    "INVALID_IDENTITY",
    "FINGERPRINT_MISMATCH",
    "UPSTREAM_VERIFICATION_FAILED",
    "UPSTREAM_STATE_MISMATCH",
    "CHAIN_MISMATCH",
    "RUNTIME_BOUNDARY_MISMATCH",
    "ADAPTER_INDEX_MISMATCH",
    "CAPABILITY_MISMATCH",
    "INVALID_UNIT_SCOPE",
    "INVALID_INTENT",
    "ALREADY_ADMITTED",
    "ALREADY_SCHEDULED",
    "EXECUTION_ALREADY_STARTED",
    "PROHIBITED_CAPABILITY_ACTIVE",
    "INVARIANT_VIOLATION",
)


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationPolicy:
    unit_scope: int = 1
    upstream_chain_layers: int = 25
    complete_chain_layers: int = 27
    runtime_boundary_kind: str = BOUNDARY_KIND
    admission_intent: str = ADMISSION_INTENT


DEFAULT_POLICY = ControlledRuntimeQueueAdmissionAuthorizationPolicy()
