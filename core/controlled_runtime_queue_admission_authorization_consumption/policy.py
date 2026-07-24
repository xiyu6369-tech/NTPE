"""Centralized immutable Stage 6.11 policy."""
from dataclasses import dataclass

REQUEST_SCHEMA_NAME="ntpe.controlled_runtime_queue_admission_authorization_consumption_request"
REQUEST_SCHEMA_VERSION="1.0"
CLAIM_SCHEMA_NAME="ntpe.controlled_runtime_queue_admission_authorization_consumption_claim"
CLAIM_SCHEMA_VERSION="1.0"
RESULT_SCHEMA_NAME="ntpe.controlled_runtime_queue_admission_authorization_consumption_result"
RESULT_SCHEMA_VERSION="1.0"
VERIFICATION_SCHEMA_NAME="ntpe.controlled_runtime_queue_admission_authorization_consumption_verification_result"
VERIFICATION_SCHEMA_VERSION="1.0"
REGISTRY_SCHEMA_NAME="ntpe.controlled_runtime_queue_admission_authorization_consumption_registry"
REGISTRY_SCHEMA_VERSION="1.0"
BOUNDARY_KIND="controlled_offline_acceptance_boundary"
CONSUMPTION_INTENT="consume_exactly_one_queue_admission_authorization"
SUCCESS_STATUS="queue_admission_authorization_consumed_not_admitted"
REASON_CODES=("INVALID_SCHEMA","INVALID_IDENTITY","FINGERPRINT_MISMATCH","UPSTREAM_VERIFICATION_FAILED","UPSTREAM_STATE_MISMATCH","CHAIN_MISMATCH","BINDING_MISMATCH","PERSISTENCE_NOT_PROVEN","CANONICAL_PAYLOAD_MISMATCH","ALREADY_CONSUMED","CONFLICT","REGISTRY_ERROR")

@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationConsumptionPolicy:
    unit_scope:int=1
    upstream_chain_layers:int=27
    complete_chain_layers:int=29
    runtime_boundary_kind:str=BOUNDARY_KIND
    consumption_intent:str=CONSUMPTION_INTENT
