from dataclasses import fields
from pathlib import Path

import core.controlled_runtime_scheduling_envelope_consumption as public
from core.controlled_runtime_scheduling_envelope_consumption.policy import (
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
)


def test_exact_public_api():
    assert public.__all__ == [
        "ControlledRuntimeSchedulingEnvelopeConsumptionRequest",
        "ControlledRuntimeSchedulingEnvelopeConsumptionClaim",
        "ControlledRuntimeSchedulingEnvelopeConsumptionResult",
        "ControlledRuntimeSchedulingEnvelopeConsumptionVerificationResult",
        "ControlledRuntimeSchedulingEnvelopeConsumptionPolicy",
        "ControlledRuntimeSchedulingEnvelopeConsumptionRegistry",
        "ControlledRuntimeSchedulingEnvelopeConsumer",
        "verify_controlled_runtime_scheduling_envelope_consumption",
        "SchedulingEnvelopeConsumptionError",
        "SchedulingEnvelopeConsumptionRequestError",
        "SchedulingEnvelopeConsumptionUpstreamError",
        "SchedulingEnvelopeConsumptionRegistryPathError",
        "SchedulingEnvelopeConsumptionRegistrySchemaError",
        "SchedulingEnvelopeConsumptionRegistryIntegrityError",
        "SchedulingEnvelopeAlreadyConsumedError",
        "SchedulingEnvelopeConsumptionConflictError",
        "SchedulingEnvelopeConsumptionCommitError",
        "SchedulingEnvelopeConsumptionVerificationError",
    ]


def test_exact_schema_constants_and_immutable_fields():
    assert (
        REQUEST_SCHEMA_NAME,
        REQUEST_SCHEMA_VERSION,
        CLAIM_SCHEMA_NAME,
        CLAIM_SCHEMA_VERSION,
        RESULT_SCHEMA_NAME,
        RESULT_SCHEMA_VERSION,
    ) == (
        "ntpe.controlled_runtime_scheduling_envelope_consumption_request",
        "1.0",
        "ntpe.controlled_runtime_scheduling_envelope_consumption_claim",
        "1.0",
        "ntpe.controlled_runtime_scheduling_envelope_consumption_result",
        "1.0",
    )
    claim_fields = {
        item.name
        for item in fields(
            public.ControlledRuntimeSchedulingEnvelopeConsumptionClaim
        )
    }
    assert {
        "scheduling_envelope_consumed",
        "scheduling_envelope_reusable",
        "queue_admission_authorized",
        "runtime_execution_scheduled",
        "queue_record_created",
        "execution_started",
        "canonical_chain",
    } <= claim_fields


def test_upstream_models_and_stage67_registry_are_not_modified():
    root = Path(__file__).resolve().parents[3]
    production = root / "core" / (
        "controlled_runtime_scheduling_envelope_consumption"
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in production.glob("*.py")
    )
    assert "controlled_runtime_atomic_scheduling_consumption.registry" not in source
    assert "AtomicSchedulingAuthorizationConsumptionRegistry" not in source
