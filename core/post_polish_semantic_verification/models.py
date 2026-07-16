from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_INPUT = "invalid_input"
    CONFLICT = "conflict"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class VerificationDecision(str, Enum):
    ACCEPT_POLISH = "accept_polish"
    ROLLBACK_TO_DRAFT = "rollback_to_draft"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCK_OUTPUT = "block_output"


@dataclass(frozen=True)
class SemanticVerificationInput:
    verification_id: str
    document_id: str
    chunk_index: int
    source_language: str
    target_language: str
    source_text: str
    source_hash: str
    verified_draft_text: str
    verified_draft_hash: str
    polish_text: str
    polish_hash: str
    polish_scope: Mapping[str, Any]
    character_memory_fingerprint: str
    context_scene_fingerprint: str
    glossary_fingerprint: str
    semantic_policy_id: str
    semantic_policy_version: str
    created_at: str


@dataclass(frozen=True)
class SemanticInvariant:
    invariant_id: str
    invariant_type: str
    source_evidence: Any
    draft_evidence: Any
    expected_value: Any
    scope: str
    confidence: float
    approval_status: str
    blocking: bool
    origin: str


@dataclass(frozen=True)
class ExtractedSemanticFeatures:
    text_hash: str
    names: tuple[str, ...]
    numbers: tuple[str, ...]
    times: tuple[str, ...]
    negations: tuple[str, ...]
    modalities: tuple[str, ...]
    causal_markers: tuple[str, ...]
    order_markers: tuple[str, ...]
    dialogue_spans: tuple[str, ...]
    paragraphs: tuple[str, ...]
    glossary_terms: tuple[str, ...]
    ambiguity_markers: tuple[str, ...]
    source_language_residue: tuple[str, ...]
    target_script_consistent: bool


@dataclass(frozen=True)
class SemanticDifference:
    difference_id: str
    difference_type: str
    source_value: Any
    draft_value: Any
    polish_value: Any
    scope: str
    evidence: Mapping[str, Any]
    confidence: float
    severity: str
    blocking: bool


@dataclass(frozen=True)
class SemanticIssue:
    issue_id: str
    issue_type: str
    severity: str
    explanation: str
    evidence: Mapping[str, Any]
    blocking: bool


@dataclass(frozen=True)
class SemanticVerificationPolicy:
    policy_id: str
    version: str
    blocking_issue_types: tuple[str, ...]
    critical_issue_types: tuple[str, ...]
    allowed_lexical_variation: tuple[str, ...]
    allowed_punctuation_changes: bool
    required_invariants: tuple[str, ...]
    minimum_evidence: int
    scope_policy: str
    ambiguity_policy: str
    glossary_policy: str
    memory_policy: str
    manual_review_policy: str


@dataclass(frozen=True)
class SemanticVerificationEvidence:
    extraction_fingerprint: str
    comparison_fingerprint: str
    invariant_fingerprint: str
    provider_executed: bool = False
    network_requests: int = 0
    new_translation_generated: bool = False


@dataclass(frozen=True)
class SemanticVerificationResult:
    status: VerificationStatus
    decision: VerificationDecision
    issues: tuple[SemanticIssue, ...]
    checked_invariants: tuple[str, ...]
    unverifiable_invariants: tuple[str, ...]
    policy_version: str
    source_hash: str
    draft_hash: str
    polish_hash: str
    deterministic_fingerprint: str
    explanation: str
    evidence: SemanticVerificationEvidence
    schema_version: str = field(default=SCHEMA_VERSION)
