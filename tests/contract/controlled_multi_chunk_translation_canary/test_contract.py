from dataclasses import fields

from core.controlled_multi_chunk_translation_canary import __all__ as public_api
from core.controlled_multi_chunk_translation_canary.models import (
    CheckpointRecord, ChunkCompletionEvidence, ChunkExecutionPlan,
    MultiChunkCanaryRequest, MultiChunkResult, MultiChunkVerificationResult,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    ATTEMPT_CAP, CHECKPOINT_SCHEMA, CHUNK_COUNT, CHUNK_EVIDENCE_SCHEMA,
    CHUNK_PLAN_SCHEMA, REQUEST_CAP, REQUEST_SCHEMA, RESULT_SCHEMA,
    VERIFICATION_SCHEMA,
)


def test_exact_public_api_and_schemas():
    assert {
        "MultiChunkCanaryRequest", "ChunkExecutionPlan",
        "ChunkCompletionEvidence", "CheckpointRecord", "MultiChunkResult",
        "MultiChunkVerificationResult", "ControlledMultiChunkExecutor",
        "resolve_multi_chunk_source", "build_multi_chunk_request",
        "write_checkpoint_atomic", "read_checkpoint", "verify_multi_chunk_result",
    }.issubset(set(public_api))
    assert (
        REQUEST_SCHEMA, CHUNK_PLAN_SCHEMA, CHUNK_EVIDENCE_SCHEMA,
        CHECKPOINT_SCHEMA, RESULT_SCHEMA, VERIFICATION_SCHEMA,
    ) == (
        "ntpe.controlled_multi_chunk_translation_request",
        "ntpe.controlled_translation_chunk_plan",
        "ntpe.controlled_translation_chunk_evidence",
        "ntpe.controlled_translation_checkpoint",
        "ntpe.controlled_multi_chunk_translation_result",
        "ntpe.controlled_multi_chunk_translation_verification_result",
    )


def test_required_model_fields_are_frozen_contract():
    assert {"chunk_ids", "chunk_fingerprints", "authenticated_lineage"}.issubset(
        {item.name for item in fields(MultiChunkCanaryRequest)}
    )
    assert {"source_start", "source_end", "previous_chunk_id", "next_chunk_id"}.issubset(
        {item.name for item in fields(ChunkExecutionPlan)}
    )
    assert {"quality_passed", "context_fingerprint", "output_fingerprint"}.issubset(
        {item.name for item in fields(ChunkCompletionEvidence)}
    )
    assert {"completed_chunk_ids", "next_expected_chunk_id"}.issubset(
        {item.name for item in fields(CheckpointRecord)}
    )
    assert {"retries", "fallbacks", "automatic_rollouts", "formal_output_replacements"}.issubset(
        {item.name for item in fields(MultiChunkResult)}
    )
    assert {"valid", "reason_codes"}.issubset(
        {item.name for item in fields(MultiChunkVerificationResult)}
    )


def test_three_chunk_sequential_zero_mutation_contract():
    assert CHUNK_COUNT == REQUEST_CAP == ATTEMPT_CAP == 3
