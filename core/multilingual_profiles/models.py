from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class SourceLanguageRules:
    subject_omission_expected: bool
    object_omission_expected: bool
    structure_risks: tuple[str, ...]
    temporal_aspect_rules: tuple[str, ...]
    culture_notes: tuple[str, ...]


@dataclass(frozen=True)
class TargetLanguageRules:
    language: str
    script: str
    dialogue_quotes: str
    requirements: tuple[str, ...]
    force_taiwan_terms: bool
    preserve_era_context: bool


@dataclass(frozen=True)
class NameHandlingPolicy:
    name_order: str
    transliteration_strategy: str
    approved_variant_policy: str
    unknown_name_policy: str
    title_policy: str
    nickname_policy: str
    full_name_completion_policy: str


@dataclass(frozen=True)
class PronounPolicy:
    subject_omission_expected: bool
    object_omission_expected: bool
    gender_marking_strength: str
    pronoun_surface_to_identity_rules: tuple[str, ...]
    unresolved_reference_policy: str
    human_approved_override: bool
    memory_evidence_policy: str


@dataclass(frozen=True)
class HonorificPolicy:
    honorific_markers: tuple[str, ...]
    register_levels: tuple[str, ...]
    relationship_implications: tuple[str, ...]
    translation_options: tuple[str, ...]
    forbidden_simplifications: tuple[str, ...]


@dataclass(frozen=True)
class DialoguePolicy:
    source_boundary_markers: tuple[str, ...]
    quote_normalization: str
    nested_quote_handling: str
    dialogue_continuation: str
    interrupted_speech: str
    unfinished_utterance: str
    speaker_attribution: str
    dialogue_to_narration_risk: bool


@dataclass(frozen=True)
class NarrativePolicy:
    era_context: str
    cultural_context: str
    narrative_distance: str
    register_preferences: tuple[str, ...]
    archaic_language_policy: str
    modernization_policy: str
    foreign_setting_policy: str


@dataclass(frozen=True)
class ResidueDetectionPolicy:
    scripts: tuple[str, ...]
    patterns: tuple[str, ...]
    allowed_categories: tuple[str, ...]
    blocking_default: bool


@dataclass(frozen=True)
class SemanticHintPolicy:
    name_patterns: tuple[str, ...]
    number_patterns: tuple[str, ...]
    time_patterns: tuple[str, ...]
    negation_markers: tuple[str, ...]
    modality_markers: tuple[str, ...]
    causal_markers: tuple[str, ...]
    dialogue_markers: tuple[str, ...]
    honorific_markers: tuple[str, ...]
    ambiguity_markers: tuple[str, ...]
    subject_omission_expected: bool


@dataclass(frozen=True)
class QualityRule:
    rule_id: str
    rule_version: str
    source_language: str
    severity: str
    blocking: bool
    evidence_required: tuple[str, ...]
    description: str
    applicability: str


@dataclass(frozen=True)
class LanguageProfile:
    profile_id: str
    profile_version: str
    schema_version: str
    source_language: str
    target_language: str
    display_name: str
    status: str
    source_rules: SourceLanguageRules
    target_rules: TargetLanguageRules
    name_policy: NameHandlingPolicy
    pronoun_policy: PronounPolicy
    honorific_policy: HonorificPolicy
    dialogue_policy: DialoguePolicy
    narrative_policy: NarrativePolicy
    residue_policy: ResidueDetectionPolicy
    semantic_hints: SemanticHintPolicy
    quality_rules: tuple[QualityRule, ...]
    created_at: str
    updated_at: str
    fingerprint: str


@dataclass(frozen=True)
class LanguageProfileIdentity:
    profile_id: str
    profile_version: str
    source_language: str
    target_language: str
    fingerprint: str


@dataclass(frozen=True)
class LanguageProfileSelection:
    status: str
    profile: LanguageProfile | None
    reason: str


@dataclass(frozen=True)
class LanguageProfileCompatibilityResult:
    compatible: bool
    stale: bool
    reasons: tuple[str, ...]
    identity: Mapping[str, Any]
