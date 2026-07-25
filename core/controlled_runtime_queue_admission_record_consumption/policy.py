"""Centralized immutable Stage 6.13 policy."""
from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_consumption_request"
REQUEST_SCHEMA_VERSION = "1.0"
CLAIM_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_consumption_claim"
CLAIM_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_consumption_result"
RESULT_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_consumption_verification_result"
VERIFICATION_SCHEMA_VERSION = "1.0"
REGISTRY_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_consumption_registry"
REGISTRY_SCHEMA_VERSION = "1.0"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
CONSUMPTION_INTENT = "consume_exactly_one_authentic_prepared_queue_admission_record"
SUCCESS_STATUS = "queue_admission_record_consumed_not_admitted"
ADMISSION_CLASS = "controlled_runtime_single_unit"
PRIORITY_CLASS = "controlled_default"
REASON_CODES = (
    "INVALID_SCHEMA",
    "INVALID_IDENTITY",
    "FINGERPRINT_MISMATCH",
    "UPSTREAM_VERIFICATION_FAILED",
    "UPSTREAM_STATE_MISMATCH",
    "CHAIN_MISMATCH",
    "BINDING_MISMATCH",
    "INVALID_UNIT_SCOPE",
    "INVALID_INTENT",
    "INVALID_ADMISSION_CLASS",
    "INVALID_PRIORITY_CLASS",
    "RECORD_NOT_PREPARED",
    "RECORD_ALREADY_CONSUMED",
    "RECORD_REUSABLE",
    "QUEUE_RECORD_ALREADY_CREATED",
    "SCHEDULING_ALREADY_STARTED",
    "EXECUTION_ALREADY_STARTED",
    "CANONICAL_PAYLOAD_MISMATCH",
    "PERSISTENCE_NOT_PROVEN",
    "ALREADY_CONSUMED",
    "CONFLICT",
    "REGISTRY_ERROR",
    "RECORD_FINGERPRINT_MISMATCH",
    "INVARIANT_VIOLATION",
)


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordConsumptionPolicy:
    unit_scope: int = 1
    upstream_chain_layers: int = 31
    complete_chain_layers: int = 33
    runtime_boundary_kind: str = BOUNDARY_KIND
    consumption_intent: str = CONSUMPTION_INTENT
    admission_class: str = ADMISSION_CLASS
    priority_class: str = PRIORITY_CLASS
    ordering_key: str = "controlled_deterministic"