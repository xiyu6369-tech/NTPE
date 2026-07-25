"""Immutable deterministic Stage 7.3 governance and evidence models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    EVIDENCE_SCHEMA_NAME, EVIDENCE_SCHEMA_VERSION, EXECUTION_INTENT,
    REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION, RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION, TARGET_LANGUAGE, TRANSLATION_PROFILE,
    VERIFICATION_SCHEMA_NAME, VERIFICATION_SCHEMA_VERSION,
)
from .serialization import canonical_json, canonical_sha256, values

_HEX = frozenset("0123456789abcdef")


def _text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _fp(name, value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in _HEX for c in value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _id(prefix, payload):
    return f"{prefix}-{canonical_sha256(payload)[:32]}"


@dataclass(frozen=True)
class ControlledTranslationExecutionRequest:
    dispatch_package_id: str
    dispatch_fingerprint: str
    schedule_id: str
    schedule_fingerprint: str
    scheduling_request_id: str
    scheduling_request_fingerprint: str
    queue_record_id: str
    queue_record_fingerprint: str
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    stage68_scheduling_envelope_id: str
    stage68_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    dispatch_key: str
    execution_plan_reference_fingerprint: str
    work_package_reference_fingerprint: str
    source_fixture_id: str
    source_fingerprint: str
    target_language: str
    translation_profile: str
    unit_scope: int
    upstream_chain: tuple[str, ...]
    execution_intent: str = EXECUTION_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    execution_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self):
        if (self.schema_name, self.schema_version) != (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION):
            raise ValueError("invalid Stage 7.3 request schema")
        for name in (
            "dispatch_package_id", "schedule_id", "scheduling_request_id",
            "queue_record_id", "stage613_claim_id", "stage612_record_id",
            "stage611_claim_id", "stage610_authorization_id",
            "stage69_consumption_claim_id", "stage68_scheduling_envelope_id",
            "stage67_consumption_claim_id", "stage66_scheduling_authorization_id",
            "runtime_boundary_id", "runtime_boundary_kind", "dispatch_key",
            "source_fixture_id",
        ):
            _text(name, getattr(self, name))
        for name in (
            "dispatch_fingerprint", "schedule_fingerprint",
            "scheduling_request_fingerprint", "queue_record_fingerprint",
            "stage613_claim_fingerprint", "stage612_record_fingerprint",
            "stage611_claim_fingerprint", "stage610_decision_fingerprint",
            "stage69_claim_fingerprint", "stage68_envelope_fingerprint",
            "stage67_claim_fingerprint", "stage66_decision_fingerprint",
            "capability_state_fingerprint", "execution_plan_reference_fingerprint",
            "work_package_reference_fingerprint", "source_fingerprint",
        ):
            _fp(name, getattr(self, name))
        if type(self.selected_adapter_index) is not int or self.selected_adapter_index < 0:
            raise ValueError("selected_adapter_index must be non-negative int")
        if type(self.unit_scope) is not int:
            raise TypeError("unit_scope must be int, not bool")
        if self.unit_scope != 1:
            raise ValueError("unit_scope must be exactly 1")
        if self.target_language != TARGET_LANGUAGE or self.translation_profile != TRANSLATION_PROFILE:
            raise ValueError("invalid target language or translation profile")
        if self.execution_intent != EXECUTION_INTENT:
            raise ValueError("invalid execution intent")
        if not isinstance(self.upstream_chain, tuple) or len(self.upstream_chain) != 38:
            raise ValueError("upstream_chain must contain exactly 38 layers")
        for index, item in enumerate(self.upstream_chain):
            _fp(f"upstream_chain[{index}]", item)
        if len(set(self.upstream_chain)) != 38 or self.upstream_chain[-1] != self.dispatch_fingerprint:
            raise ValueError("invalid Stage 7.2 chain")
        identity = _id(
            "stage73-execution-request",
            values(self, exclude=("execution_request_id", "request_fingerprint")),
        )
        object.__setattr__(self, "execution_request_id", identity)
        object.__setattr__(
            self, "request_fingerprint",
            canonical_sha256(values(self, exclude=("request_fingerprint",))),
        )

    def to_json(self):
        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledTranslationExecutionResult:
    request: ControlledTranslationExecutionRequest
    provider: str
    provider_model: str
    output_artifact_path: str
    output_artifact_fingerprint: str
    output_character_count: int
    quality_passed: bool
    structural_quality_passed: bool
    baseline_quality_passed: bool
    execution_started: bool
    runtime_executor_invoked: bool
    provider_execution_started: bool
    translation_execution_started: bool
    output_written: bool
    runtime_executions_started: int
    provider_requests: int
    provider_attempts: int
    provider_successes: int
    translation_executions: int
    controlled_outputs_written: int
    additional_chunks_started: int
    retries: int
    fallbacks: int
    automatic_rollouts: int
    formal_output_replacements: int
    resume_mutations: int
    cache_mutations: int
    canonical_chain: tuple[str, ...]
    schema_name: str = RESULT_SCHEMA_NAME
    schema_version: str = RESULT_SCHEMA_VERSION
    execution_result_id: str = field(default="", init=False)
    result_fingerprint: str = field(default="", init=False)

    def __post_init__(self):
        if (self.schema_name, self.schema_version) != (RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION):
            raise ValueError("invalid Stage 7.3 result schema")
        if not isinstance(self.request, ControlledTranslationExecutionRequest):
            raise TypeError("request must be Stage 7.3 request")
        _text("provider", self.provider)
        _text("provider_model", self.provider_model)
        _text("output_artifact_path", self.output_artifact_path)
        _fp("output_artifact_fingerprint", self.output_artifact_fingerprint)
        positive = (
            "runtime_executions_started", "provider_requests", "provider_attempts",
            "provider_successes", "translation_executions", "controlled_outputs_written",
        )
        zero = (
            "additional_chunks_started", "retries", "fallbacks",
            "automatic_rollouts", "formal_output_replacements",
            "resume_mutations", "cache_mutations",
        )
        if any(getattr(self, name) != 1 for name in positive):
            raise ValueError("success counters must equal 1")
        if any(getattr(self, name) != 0 for name in zero):
            raise ValueError("prohibited counters must equal 0")
        if type(self.output_character_count) is not int or self.output_character_count <= 0:
            raise ValueError("output_character_count must be positive")
        for name in (
            "quality_passed", "structural_quality_passed", "baseline_quality_passed",
            "execution_started", "runtime_executor_invoked",
            "provider_execution_started", "translation_execution_started",
            "output_written",
        ):
            if getattr(self, name) is not True:
                raise ValueError(f"{name} must be true")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (39, 40):
            raise ValueError("result chain must have 39 or 40 layers")
        pre = self.canonical_chain[:39]
        if pre[-1] != self.request.request_fingerprint or len(set(pre)) != 39:
            raise ValueError("execution request must precede result")
        identity = _id("stage73-execution-result", self._payload(pre, ""))
        object.__setattr__(self, "execution_result_id", identity)
        fingerprint = canonical_sha256(self._payload(pre, identity))
        object.__setattr__(self, "result_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre + (fingerprint,))

    def _payload(self, chain, identity):
        payload = values(
            self, exclude=("execution_result_id", "result_fingerprint", "canonical_chain")
        )
        payload["execution_result_id"] = identity
        payload["canonical_chain"] = list(chain)
        return payload

    def to_json(self):
        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledTranslationOutputEvidence:
    execution_result_id: str
    execution_result_fingerprint: str
    execution_request_id: str
    execution_request_fingerprint: str
    source_fixture_id: str
    source_fingerprint: str
    source_character_count: int
    chunk_count: int
    output_artifact_path: str
    output_artifact_fingerprint: str
    output_character_count: int
    hangul_character_count: int
    hangul_ratio: float
    source_echo_detected: bool
    duplicate_output_detected: bool
    corruption_detected: bool
    traditional_chinese_signal: bool
    dialogue_punctuation_passed: bool
    fixed_names_passed: bool
    quality_passed: bool
    canonical_chain: tuple[str, ...]
    schema_name: str = EVIDENCE_SCHEMA_NAME
    schema_version: str = EVIDENCE_SCHEMA_VERSION
    evidence_fingerprint: str = field(default="", init=False)

    def __post_init__(self):
        if (self.schema_name, self.schema_version) != (EVIDENCE_SCHEMA_NAME, EVIDENCE_SCHEMA_VERSION):
            raise ValueError("invalid Stage 7.3 evidence schema")
        for name in (
            "execution_result_id", "execution_request_id", "source_fixture_id",
            "output_artifact_path",
        ):
            _text(name, getattr(self, name))
        for name in (
            "execution_result_fingerprint", "execution_request_fingerprint",
            "source_fingerprint", "output_artifact_fingerprint",
        ):
            _fp(name, getattr(self, name))
        if self.chunk_count != 1 or self.source_character_count <= 0 or self.output_character_count <= 0:
            raise ValueError("evidence scope invariant violated")
        if self.hangul_character_count < 0 or self.hangul_ratio < 0:
            raise ValueError("invalid residual metrics")
        if (
            self.source_echo_detected or self.duplicate_output_detected
            or self.corruption_detected or not self.traditional_chinese_signal
            or not self.dialogue_punctuation_passed or not self.fixed_names_passed
            or not self.quality_passed
        ):
            raise ValueError("successful evidence quality invariant violated")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (40, 41):
            raise ValueError("evidence chain must have 40 or 41 layers")
        pre = self.canonical_chain[:40]
        if pre[-1] != self.execution_result_fingerprint or len(set(pre)) != 40:
            raise ValueError("execution result must precede evidence")
        fingerprint = canonical_sha256(
            values(self, exclude=("evidence_fingerprint", "canonical_chain"))
            | {"canonical_chain": list(pre)}
        )
        object.__setattr__(self, "evidence_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre + (fingerprint,))

    def to_json(self):
        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledTranslationVerificationResult:
    valid: bool
    schema_verified: bool
    identity_verified: bool
    binding_verified: bool
    chain_verified: bool
    scope_verified: bool
    provider_counts_verified: bool
    output_verified: bool
    quality_verified: bool
    state_verified: bool
    prohibited_counters_verified: bool
    reason_codes: tuple[str, ...]
    schema_name: str = VERIFICATION_SCHEMA_NAME
    schema_version: str = VERIFICATION_SCHEMA_VERSION

    def __post_init__(self):
        if (self.schema_name, self.schema_version) != (VERIFICATION_SCHEMA_NAME, VERIFICATION_SCHEMA_VERSION):
            raise ValueError("invalid Stage 7.3 verification schema")
        for name in (
            "valid", "schema_verified", "identity_verified", "binding_verified",
            "chain_verified", "scope_verified", "provider_counts_verified",
            "output_verified", "quality_verified", "state_verified",
            "prohibited_counters_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be tuple")
