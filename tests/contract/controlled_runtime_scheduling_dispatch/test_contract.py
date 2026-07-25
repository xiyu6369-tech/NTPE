from dataclasses import fields

import core.controlled_runtime_scheduling_dispatch as api
from core.controlled_runtime_scheduling_dispatch import policy


def test_exact_public_api():
    assert api.__all__ == [
        "ControlledRuntimeSchedulingRequest",
        "ControlledRuntimeExecutionSchedule",
        "ControlledRuntimeDispatchPackage",
        "ControlledRuntimeSchedulingResult",
        "ControlledRuntimeSchedulingDispatchVerificationResult",
        "ControlledRuntimeSchedulingPolicy",
        "ControlledRuntimeSchedulingRegistry",
        "ControlledRuntimeScheduler",
        "verify_controlled_runtime_scheduling_dispatch",
        "ControlledRuntimeSchedulingDispatchError",
        "ControlledRuntimeSchedulingDispatchPathError",
        "ControlledRuntimeSchedulingDispatchSchemaError",
        "ControlledRuntimeSchedulingDispatchIntegrityError",
        "ControlledRuntimeSchedulingDispatchPolicyError",
        "ControlledRuntimeAlreadyScheduledError",
        "ControlledRuntimeSchedulingConflictError",
        "ControlledRuntimeSchedulingCommitError",
        "ControlledRuntimeSchedulingDispatchVerificationError",
    ]
    assert not any(
        word in api.__all__
        for word in ("RuntimeExecutor", "Worker", "Provider", "Translation")
    )


def test_exact_schemas_versions_and_reasons():
    assert (
        policy.REQUEST_SCHEMA_NAME,
        policy.SCHEDULE_SCHEMA_NAME,
        policy.DISPATCH_SCHEMA_NAME,
        policy.RESULT_SCHEMA_NAME,
        policy.VERIFICATION_SCHEMA_NAME,
    ) == (
        "ntpe.controlled_runtime_scheduling_request",
        "ntpe.controlled_runtime_execution_schedule",
        "ntpe.controlled_runtime_dispatch_package",
        "ntpe.controlled_runtime_scheduling_result",
        "ntpe.controlled_runtime_scheduling_dispatch_verification_result",
    )
    assert {
        policy.REQUEST_SCHEMA_VERSION,
        policy.SCHEDULE_SCHEMA_VERSION,
        policy.DISPATCH_SCHEMA_VERSION,
        policy.RESULT_SCHEMA_VERSION,
        policy.VERIFICATION_SCHEMA_VERSION,
    } == {"1.0"}
    assert len(policy.REASON_CODES) == len(set(policy.REASON_CODES))


def test_models_expose_references_not_payloads():
    names = {
        field.name
        for model in (
            api.ControlledRuntimeSchedulingRequest,
            api.ControlledRuntimeExecutionSchedule,
            api.ControlledRuntimeDispatchPackage,
        )
        for field in fields(model)
    }
    assert {
        "execution_plan_reference_fingerprint",
        "work_package_reference_fingerprint",
    } <= names
    assert not names & {
        "source_text", "prompt", "glossary", "credentials",
        "provider_payload", "translated_output", "worker", "executor",
    }
