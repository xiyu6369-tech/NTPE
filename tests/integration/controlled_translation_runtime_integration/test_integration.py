from core.controlled_translation_runtime_integration import (
    ControlledTranslationExecutor, verify_controlled_translation_runtime_execution,
)
from tests.unit.controlled_translation_runtime_integration import build_context


def test_full_stage72_to_controlled_output_flow(tmp_path):
    context = build_context(tmp_path)
    result, evidence = ControlledTranslationExecutor().execute(**context)
    verification = verify_controlled_translation_runtime_execution(
        context["request"], result, evidence,
        dispatch_package=context["dispatch_package"],
        artifact_root=context["artifact_root"],
    )
    assert verification.valid
    assert (
        result.runtime_executions_started, result.provider_requests,
        result.provider_attempts, result.provider_successes,
        result.translation_executions, result.controlled_outputs_written,
    ) == (1, 1, 1, 1, 1, 1)
    assert (
        result.additional_chunks_started, result.retries, result.fallbacks,
        result.automatic_rollouts, result.formal_output_replacements,
        result.resume_mutations, result.cache_mutations,
    ) == (0, 0, 0, 0, 0, 0, 0)
