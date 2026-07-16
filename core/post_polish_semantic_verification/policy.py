from __future__ import annotations

from dataclasses import asdict

from .models import SemanticVerificationPolicy

POLICY_ID = "semantic-verification-policy"
POLICY_VERSION = "1.0"

INVARIANT_TYPES = (
    "subject_identity", "pronoun_reference", "named_entity", "name_form", "number",
    "time_expression", "negation", "modality", "causal_relation", "relationship",
    "speaker", "point_of_view", "location", "event_presence", "event_order",
    "action_agent", "action_patient", "dialogue_boundary", "paragraph_boundary",
    "glossary_term", "ambiguity_preservation", "scope_integrity", "omission",
    "addition", "source_language_residue", "target_script_consistency",
)

BLOCKING_ISSUES = (
    "subject_identity", "pronoun_reference", "named_entity", "name_completion",
    "number", "time_expression", "negation", "modality", "causal_relation",
    "relationship", "speaker", "point_of_view", "location", "event_presence",
    "event_order", "action_agent", "action_patient", "dialogue_boundary",
    "glossary_term", "ambiguity_loss", "omission", "addition", "out_of_scope_change",
    "source_language_residue", "target_script_consistency",
)

DEFAULT_POLICY = SemanticVerificationPolicy(
    policy_id=POLICY_ID,
    version=POLICY_VERSION,
    blocking_issue_types=BLOCKING_ISSUES,
    critical_issue_types=("subject_identity", "negation", "action_agent", "action_patient"),
    allowed_lexical_variation=("nonsemantic_particle", "word_order_only"),
    allowed_punctuation_changes=True,
    required_invariants=("number", "time_expression", "negation", "modality", "causal_relation", "dialogue_boundary", "paragraph_boundary", "ambiguity_preservation", "scope_integrity"),
    minimum_evidence=5,
    scope_policy="outside-span-must-be-byte-equivalent",
    ambiguity_policy="preserve-unless-human-approved",
    glossary_policy="approved-form-only",
    memory_policy="selected-human-approved-evidence-only",
    manual_review_policy="unverifiable-or-new-ambiguity",
)


def policy_as_dict(policy: SemanticVerificationPolicy = DEFAULT_POLICY) -> dict:
    return asdict(policy)


def get_policy(policy_id: str = POLICY_ID, version: str = POLICY_VERSION) -> SemanticVerificationPolicy:
    if policy_id != POLICY_ID or version != POLICY_VERSION:
        raise ValueError("unknown semantic verification policy")
    return DEFAULT_POLICY
