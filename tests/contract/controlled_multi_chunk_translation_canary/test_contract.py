from dataclasses import fields

from core.controlled_multi_chunk_translation_canary import __all__ as public_api
from core.controlled_multi_chunk_translation_canary.models import (
    CheckpointRecord, ChunkCompletionEvidence, ChunkExecutionPlan,
    ChunkQualityAssessment, ChunkQualityVerificationResult,
    MultiChunkCanaryRequest, MultiChunkResult, MultiChunkVerificationResult,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    ATTEMPT_CAP, CHECKPOINT_SCHEMA, CHUNK_COUNT, CHUNK_EVIDENCE_SCHEMA,
    CHUNK_EVIDENCE_SCHEMA_VERSION,
    CHUNK_PLAN_SCHEMA, CHUNK_QUALITY_SCHEMA, REQUEST_CAP, REQUEST_SCHEMA,
    REQUEST_SCHEMA_VERSION, RESULT_SCHEMA, SOURCE_FINGERPRINT_TYPE,
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
    assert {
        "chunk_ids", "chunk_fingerprints", "authenticated_lineage",
        "source_fingerprint_type", "complete_source_fingerprint_type",
    }.issubset({item.name for item in fields(MultiChunkCanaryRequest)})
    assert REQUEST_SCHEMA_VERSION == "1.1"
    assert SOURCE_FINGERPRINT_TYPE == "sha256-canonical-json-v1"
    assert {"source_start", "source_end", "previous_chunk_id", "next_chunk_id"}.issubset(
        {item.name for item in fields(ChunkExecutionPlan)}
    )
    assert CHUNK_EVIDENCE_SCHEMA_VERSION == "1.1"
    assert {
        "quality_passed", "context_fingerprint", "output_fingerprint",
        "raw_provider_candidate_fingerprint", "authentic_formatter_fingerprint",
        "dialogue_normalized_fingerprint", "dialogue_normalization_applied",
        "dialogue_normalization_pair_count",
    }.issubset(
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

def test_exact_quality_assessment_contract():
    assert CHUNK_QUALITY_SCHEMA == "ntpe.controlled_translation_chunk_quality_assessment"
    assert {
        "non_empty", "minimum_output_length_passed", "hangul_residual_passed",
        "no_source_echo", "no_duplicate_loop", "no_corruption",
        "traditional_chinese_signal", "dialogue_punctuation_passed",
        "fixed_names_passed", "no_prohibited_prefix", "structural_passed",
        "baseline_passed", "quality_passed",
    } == {item.name for item in fields(ChunkQualityAssessment) if item.init}
    assert {"valid", "reason_codes", "assessment_fingerprint"} == {
        item.name for item in fields(ChunkQualityVerificationResult)
    }
