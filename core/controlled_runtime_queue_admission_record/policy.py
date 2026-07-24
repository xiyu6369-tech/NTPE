"""Centralized immutable Stage 6.12 policy."""
from dataclasses import dataclass

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_request"
REQUEST_SCHEMA_VERSION = "1.0"
RECORD_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record"
RECORD_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_result"
RESULT_SCHEMA_VERSION = "1.0"
VERIFICATION_SCHEMA_NAME = "ntpe.controlled_runtime_queue_admission_record_verification_result"
VERIFICATION_SCHEMA_VERSION = "1.0"
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
PREPARATION_INTENT = "prepare_exactly_one_immutable_queue_admission_record"
SUCCESS_STATUS = "queue_admission_record_prepared_not_admitted"
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
    "AUTHORIZATION_NOT_GRANTED",
    "AUTHORIZATION_NOT_CONSUMED",
    "AUTHORIZATION_REUSABLE",
    "RECORD_ALREADY_PREPARED",
    "QUEUE_RECORD_ALREADY_CREATED",
    "SCHEDULING_ALREADY_STARTED",
    "EXECUTION_ALREADY_STARTED",
    "PROHIBITED_CAPABILITY_ACTIVE",
    "INVARIANT_VIOLATION",
)

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordPolicy:
    unit_scope: int = 1
    upstream_chain_layers: int = 29
    complete_chain_layers: int = 31
    runtime_boundary_kind: str = BOUNDARY_KIND
    preparation_intent: str = PREPARATION_INTENT
    admission_class: str = ADMISSION_CLASS
    priority_class: str = PRIORITY_CLASS
