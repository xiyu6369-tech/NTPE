"""Immutable deterministic Stage 7.4 models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from core.controlled_translation_runtime_integration.serialization import (
    canonical_json, canonical_sha256,
)

from .policy import (
    ATTEMPT_CAP, CHECKPOINT_SCHEMA, CHUNK_COUNT, CHUNK_EVIDENCE_SCHEMA,
    CHUNK_PLAN_SCHEMA, CHUNK_QUALITY_SCHEMA, CONNECT_TIMEOUT_SECONDS, INTENT,
    PROFILE, REQUEST_CAP,
    REQUEST_SCHEMA, REQUEST_SCHEMA_VERSION, RESULT_SCHEMA, READ_TIMEOUT_SECONDS,
    SCHEMA_VERSION, SOURCE_FINGERPRINT_TYPE, TARGET_LANGUAGE,
    VERIFICATION_SCHEMA,
)


def _identifier(prefix: str, value: object) -> str:
    return f"{prefix}-{canonical_sha256(value)[:32]}"


def _require_fp(name: str, value: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be sha256")
    int(value, 16)


@dataclass(frozen=True)
class ChunkExecutionPlan:
    index: int
    chunk_id: str
    chunk_fingerprint: str
    source_start: int
    source_end: int
    source_character_count: int
    source_fixture_id: str
    source_fingerprint: str
    previous_chunk_id: str
    next_chunk_id: str
    target_language: str
    literary_profile: str
    work_package_reference_fingerprint: str
    output_artifact_path: str
    checkpoint_artifact_path: str
    schema: str = field(default=CHUNK_PLAN_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if self.index not in (1, 2, 3) or self.source_start < 0:
            raise ValueError("invalid chunk index or start")
        if self.source_end - self.source_start != self.source_character_count:
            raise ValueError("invalid chunk range")
        if self.source_character_count < 1:
            raise ValueError("chunk must be non-empty")
        _require_fp("chunk_fingerprint", self.chunk_fingerprint)
        _require_fp("source_fingerprint", self.source_fingerprint)
        _require_fp(
            "work_package_reference_fingerprint",
            self.work_package_reference_fingerprint,
        )

    @property
    def plan_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class MultiChunkCanaryRequest:
    stage73_policy_fingerprint: str
    dispatch_package_id: str
    dispatch_fingerprint: str
    schedule_id: str
    schedule_fingerprint: str
    queue_record_id: str
    queue_record_fingerprint: str
    authenticated_lineage: tuple[str, ...]
    source_fixture_id: str
    source_fingerprint: str
    source_fingerprint_type: str
    complete_source_fingerprint: str
    complete_source_fingerprint_type: str
    target_language: str
    literary_profile: str
    chunk_count: int
    chunk_ids: tuple[str, ...]
    chunk_fingerprints: tuple[str, ...]
    provider_request_cap: int
    provider_attempt_cap: int
    connect_timeout_seconds: int
    read_timeout_seconds: int
    artifact_root: str
    intent: str
    schema: str = field(default=REQUEST_SCHEMA, init=False)
    version: str = field(default=REQUEST_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "authenticated_lineage", tuple(self.authenticated_lineage))
        object.__setattr__(self, "chunk_ids", tuple(self.chunk_ids))
        object.__setattr__(self, "chunk_fingerprints", tuple(self.chunk_fingerprints))
        if (
            self.chunk_count != CHUNK_COUNT
            or len(self.chunk_ids) != CHUNK_COUNT
            or len(set(self.chunk_ids)) != CHUNK_COUNT
            or len(self.chunk_fingerprints) != CHUNK_COUNT
            or len(set(self.chunk_fingerprints)) != CHUNK_COUNT
        ):
            raise ValueError("request must bind exactly three unique chunks")
        if (
            self.provider_request_cap != REQUEST_CAP
            or self.provider_attempt_cap != ATTEMPT_CAP
            or self.connect_timeout_seconds != CONNECT_TIMEOUT_SECONDS
            or self.read_timeout_seconds != READ_TIMEOUT_SECONDS
            or self.target_language != TARGET_LANGUAGE
            or self.literary_profile != PROFILE
            or self.intent != INTENT
            or self.source_fingerprint_type != SOURCE_FINGERPRINT_TYPE
            or self.complete_source_fingerprint_type != SOURCE_FINGERPRINT_TYPE
        ):
            raise ValueError("request policy mismatch")
        for name in (
            "stage73_policy_fingerprint", "dispatch_fingerprint",
            "schedule_fingerprint", "queue_record_fingerprint",
            "source_fingerprint", "complete_source_fingerprint",
        ):
            _require_fp(name, getattr(self, name))

    @property
    def request_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))

    @property
    def request_id(self) -> str:
        return _identifier("stage74-multi-chunk-request", asdict(self))


@dataclass(frozen=True)
class ChunkCompletionEvidence:
    request_id: str
    request_fingerprint: str
    chunk_id: str
    chunk_fingerprint: str
    index: int
    output_artifact_path: str
    output_fingerprint: str
    output_character_count: int
    context_character_count: int
    context_fingerprint: str
    hangul_character_count: int
    source_echo_detected: bool
    duplicate_output_detected: bool
    corruption_detected: bool
    traditional_chinese_signal: bool
    dialogue_punctuation_passed: bool
    fixed_names_passed: bool
    quality_passed: bool
    provider_requests: int = 1
    provider_attempts: int = 1
    provider_successes: int = 1
    retries: int = 0
    fallbacks: int = 0
    schema: str = field(default=CHUNK_EVIDENCE_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    @property
    def evidence_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class ChunkQualityAssessment:
    non_empty: bool
    minimum_output_length_passed: bool
    hangul_residual_passed: bool
    no_source_echo: bool
    no_duplicate_loop: bool
    no_corruption: bool
    traditional_chinese_signal: bool
    dialogue_punctuation_passed: bool
    fixed_names_passed: bool
    no_prohibited_prefix: bool
    structural_passed: bool
    baseline_passed: bool
    quality_passed: bool
    schema: str = field(default=CHUNK_QUALITY_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        mandatory = (
            self.non_empty,
            self.minimum_output_length_passed,
            self.hangul_residual_passed,
            self.no_source_echo,
            self.no_duplicate_loop,
            self.no_corruption,
            self.traditional_chinese_signal,
            self.dialogue_punctuation_passed,
            self.fixed_names_passed,
            self.no_prohibited_prefix,
            self.structural_passed,
            self.baseline_passed,
        )
        if any(type(value) is not bool for value in (*mandatory, self.quality_passed)):
            raise TypeError("quality fields must be exact bool")
        if self.quality_passed is not all(value is True for value in mandatory):
            raise ValueError("quality aggregate does not match mandatory fields")

    @property
    def assessment_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class ChunkQualityVerificationResult:
    valid: bool
    reason_codes: tuple[str, ...]
    assessment_fingerprint: str

    def __post_init__(self) -> None:
        if type(self.valid) is not bool:
            raise TypeError("valid must be exact bool")
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))

@dataclass(frozen=True)
class CheckpointRecord:
    request_id: str
    request_fingerprint: str
    source_fixture_id: str
    source_fingerprint: str
    total_planned_chunks: int
    completed_chunk_count: int
    completed_chunk_ids: tuple[str, ...]
    output_fingerprints: tuple[str, ...]
    last_completed_chunk_id: str
    next_expected_chunk_id: str
    provider_request_count: int
    provider_success_count: int
    translation_execution_count: int
    artifact_paths: tuple[str, ...]
    resume_execution_attempts: int = 0
    schema: str = field(default=CHECKPOINT_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "completed_chunk_ids", tuple(self.completed_chunk_ids))
        object.__setattr__(self, "output_fingerprints", tuple(self.output_fingerprints))
        object.__setattr__(self, "artifact_paths", tuple(self.artifact_paths))
        if (
            self.total_planned_chunks != CHUNK_COUNT
            or self.completed_chunk_count not in (1, 2, 3)
            or len(self.completed_chunk_ids) != self.completed_chunk_count
            or len(self.output_fingerprints) != self.completed_chunk_count
            or self.provider_request_count != self.completed_chunk_count
            or self.provider_success_count != self.completed_chunk_count
            or self.translation_execution_count != self.completed_chunk_count
            or self.resume_execution_attempts != 0
        ):
            raise ValueError("checkpoint invariant failed")

    @property
    def checkpoint_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class MultiChunkResult:
    request_id: str
    request_fingerprint: str
    chunk_evidence: tuple[ChunkCompletionEvidence, ...]
    combined_output_path: str
    combined_output_fingerprint: str
    chunks_planned: int
    chunks_started: int
    chunks_completed: int
    provider_requests: int
    provider_attempts: int
    provider_successes: int
    translation_executions: int
    chunk_outputs_written: int
    checkpoints_written: int
    combined_output_written: int
    retries: int = 0
    fallbacks: int = 0
    parallel_requests: int = 0
    automatic_rollouts: int = 0
    formal_output_replacements: int = 0
    resume_execution_attempts: int = 0
    cache_mutations: int = 0
    schema: str = field(default=RESULT_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "chunk_evidence", tuple(self.chunk_evidence))

    @property
    def result_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))


@dataclass(frozen=True)
class MultiChunkVerificationResult:
    valid: bool
    reason_codes: tuple[str, ...]
    request_id: str
    result_fingerprint: str
    schema: str = field(default=VERIFICATION_SCHEMA, init=False)
    version: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))

    @property
    def verification_fingerprint(self) -> str:
        return canonical_sha256(asdict(self))
