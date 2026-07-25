from dataclasses import fields

import core.controlled_translation_runtime_integration as api
from core.controlled_translation_runtime_integration import policy


def test_exact_public_api():
    assert api.__all__ == [
        "ControlledTranslationExecutionRequest",
        "ControlledTranslationExecutionResult",
        "ControlledTranslationOutputEvidence",
        "ControlledTranslationVerificationResult",
        "ControlledTranslationExecutionPolicy",
        "ControlledDispatchWorkPackageResolver",
        "ControlledTranslationExecutor",
        "verify_controlled_translation_runtime_execution",
        "ControlledTranslationRuntimeError",
        "ControlledTranslationDispatchVerificationError",
        "ControlledTranslationResolutionError",
        "ControlledTranslationSourceIntegrityError",
        "ControlledTranslationMultipleChunkError",
        "ControlledTranslationProviderConfigurationError",
        "ControlledTranslationProviderTimeoutError",
        "ControlledTranslationProviderRequestError",
        "ControlledTranslationProviderResponseError",
        "ControlledTranslationQualityError",
        "ControlledTranslationOutputError",
        "ControlledTranslationVerificationError",
    ]


def test_exact_schemas_and_one_request_policy():
    assert (
        policy.REQUEST_SCHEMA_NAME, policy.RESULT_SCHEMA_NAME,
        policy.EVIDENCE_SCHEMA_NAME, policy.VERIFICATION_SCHEMA_NAME,
    ) == (
        "ntpe.controlled_translation_runtime_execution_request",
        "ntpe.controlled_translation_runtime_execution_result",
        "ntpe.controlled_translation_runtime_output_evidence",
        "ntpe.controlled_translation_runtime_verification_result",
    )
    p = api.ControlledTranslationExecutionPolicy()
    assert (p.provider_requests, p.provider_attempts, p.retries, p.fallbacks) == (1, 1, 0, 0)


def test_result_contract_has_exact_state_and_zero_counters():
    names = {item.name for item in fields(api.ControlledTranslationExecutionResult)}
    assert {
        "execution_started", "runtime_executor_invoked",
        "provider_execution_started", "translation_execution_started",
        "output_written", "automatic_rollouts", "formal_output_replacements",
        "resume_mutations", "cache_mutations",
    } <= names
