"""Immutable Stage 6.9 policy and schema constants."""

from dataclasses import dataclass

REQUEST_SCHEMA_NAME = (
    "ntpe.controlled_runtime_scheduling_envelope_consumption_request"
)
REQUEST_SCHEMA_VERSION = "1.0"
CLAIM_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_envelope_consumption_claim"
CLAIM_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_envelope_consumption_result"
RESULT_SCHEMA_VERSION = "1.0"
REGISTRY_SCHEMA_NAME = (
    "ntpe.controlled_runtime_scheduling_envelope_consumption_registry"
)
REGISTRY_SCHEMA_VERSION = "1.0"
REGISTRY_COMPONENT = (
    "ntpe.stage6.9.controlled_runtime_scheduling_envelope_consumption"
)
BOUNDARY_KIND = "controlled_offline_acceptance_boundary"
SUCCESS_STATUS = "scheduling_envelope_consumed_not_admitted_not_scheduled"


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeConsumptionPolicy:
    unit_scope: int = 1
    upstream_chain_layers: int = 23
    complete_chain_layers: int = 25
    runtime_boundary_kind: str = BOUNDARY_KIND


DEFAULT_POLICY = ControlledRuntimeSchedulingEnvelopeConsumptionPolicy()
