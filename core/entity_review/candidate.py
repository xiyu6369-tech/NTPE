"""RM-7.3.2 P4 — Review Candidate Factory.

Creates ReviewCandidate instances from EntityMismatch with full evidence.
No auto-learning. No provider. No network.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from core.entity_consistency.models import EntityMismatch
from core.entity_consistency.matching_policy import FormAwareMatchingPolicy, MatchResult, NameFormType
from core.entity_normalization.models import NameFormType as NormalizationNameFormType
from core.entity_review.models import (
    CandidateOrigin,
    Evidence,
    FormType,
    ReviewCandidate,
    ReviewStatus,
)
from core.knowledge_evolution.models import EntityType, Severity


def _map_name_form_type(nf_type: Optional[NameFormType]) -> FormType:
    """Map matching policy NameFormType to Review FormType."""
    if nf_type is None:
        return FormType.FULL_NAME
    mapping = {
        NameFormType.FULL_NAME: FormType.FULL_NAME,
        NameFormType.GIVEN_NAME: FormType.GIVEN_NAME,
        NameFormType.FAMILY_NAME: FormType.FAMILY_NAME,
        NameFormType.NICKNAME: FormType.NICKNAME,
        NameFormType.TITLE: FormType.TITLE,
        NameFormType.FORMAL: FormType.FORMAL,
        NameFormType.INTIMATE: FormType.INTIMATE,
        NameFormType.RELATIONSHIP: FormType.RELATIONSHIP,
    }
    return mapping.get(nf_type, FormType.FULL_NAME)


def _map_normalization_form_type(nf_type: Optional[NormalizationNameFormType]) -> FormType:
    """Map normalization NameFormType to Review FormType."""
    if nf_type is None:
        return FormType.FULL_NAME
    mapping = {
        NormalizationNameFormType.FULL_NAME: FormType.FULL_NAME,
        NormalizationNameFormType.GIVEN_NAME: FormType.GIVEN_NAME,
        NormalizationNameFormType.FAMILY_NAME: FormType.FAMILY_NAME,
        NormalizationNameFormType.NICKNAME: FormType.NICKNAME,
        NormalizationNameFormType.TITLE: FormType.TITLE,
        NormalizationNameFormType.FORMAL: FormType.FORMAL,
        NormalizationNameFormType.INTIMATE: FormType.INTIMATE,
        NormalizationNameFormType.RELATIONSHIP: FormType.RELATIONSHIP,
    }
    return mapping.get(nf_type, FormType.FULL_NAME)


def _infer_form_type_from_source(source: str, entity_type: EntityType,
                                 matching_policy: Optional[FormAwareMatchingPolicy] = None) -> FormType:
    """Infer the form type from source text and entity type."""
    if entity_type != EntityType.CHARACTER:
        return FormType.FULL_NAME

    if matching_policy:
        for form_type in FormType:
            nf_type = _form_type_to_matching_policy(form_type)
            if nf_type and matching_policy.get_spec(nf_type):
                spec = matching_policy.get_spec(nf_type)
                if spec and spec.allowed_patterns:
                    for allowed in spec.allowed_patterns:
                        if allowed and allowed in source:
                            return form_type

    # Fallback inference from source text
    formal_suffixes = ["先生", "氏", "様", "さん", "씨", "님", "선생"]
    for suffix in formal_suffixes:
        if source.endswith(suffix):
            return FormType.FORMAL

    intimate_suffixes = ["啊", "呀", "啦", "喔", "耶", "야", "아", "이"]
    for suffix in intimate_suffixes:
        if source.endswith(suffix):
            return FormType.INTIMATE

    if len(source) == 1:
        return FormType.FAMILY_NAME
    if len(source) == 2:
        return FormType.GIVEN_NAME
    return FormType.FULL_NAME


def _form_type_to_matching_policy(form_type: FormType) -> Optional[NameFormType]:
    """Convert Review FormType to matching policy NameFormType."""
    mapping = {
        FormType.FULL_NAME: NameFormType.FULL_NAME,
        FormType.GIVEN_NAME: NameFormType.GIVEN_NAME,
        FormType.FAMILY_NAME: NameFormType.FAMILY_NAME,
        FormType.NICKNAME: NameFormType.NICKNAME,
        FormType.TITLE: NameFormType.TITLE,
        FormType.FORMAL: NameFormType.FORMAL,
        FormType.INTIMATE: NameFormType.INTIMATE,
        FormType.RELATIONSHIP: NameFormType.RELATIONSHIP,
    }
    return mapping.get(form_type)


def _generate_candidate_id(entity_id: str, form_type: FormType,
                           expected: str, actual: str, rule: str,
                           source_context: str) -> str:
    """Generate deterministic candidate ID for deduplication."""
    content = f"{entity_id}|{form_type.value}|{expected}|{actual}|{rule}|{source_context}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _build_match_rule(mismatch: EntityMismatch, form_type: FormType,
                      matching_policy: Optional[FormAwareMatchingPolicy] = None) -> str:
    """Build a descriptive rule name for the mismatch."""
    if matching_policy:
        nf_type = _form_type_to_matching_policy(form_type)
        if nf_type:
            spec = matching_policy.get_spec(nf_type)
            if spec and spec.forbidden_patterns:
                for forbidden in spec.forbidden_patterns:
                    if forbidden and mismatch.found and forbidden in mismatch.found:
                        return f"{form_type.value}_FORBIDS_{nf_type.value}_EXPANSION"
            if spec and spec.allowed_patterns:
                allowed_found = False
                for allowed in spec.allowed_patterns:
                    if allowed and mismatch.found and allowed in mismatch.found:
                        allowed_found = True
                        break
                if not allowed_found:
                    return f"{form_type.value}_REQUIRES_EXACT_MATCH"

    # Fallback rules based on form type
    if form_type == FormType.GIVEN_NAME and mismatch.found:
        return "GIVEN_NAME_FORBIDS_FULL_NAME"
    if form_type == FormType.FAMILY_NAME and mismatch.found:
        return "FAMILY_NAME_FORBIDS_FULL_NAME"
    if form_type == FormType.INTIMATE and mismatch.found:
        return "INTIMATE_ONLY_GIVEN_PLUS_SUFFIX"
    return "ENTITY_CONSISTENCY_MISMATCH"


def _build_evidence(mismatch: EntityMismatch, form_type: FormType,
                    matching_policy: Optional[FormAwareMatchingPolicy] = None,
                    policy_detail: Optional[Dict[str, Any]] = None) -> Evidence:
    """Build structured evidence from mismatch."""
    metadata = dict(mismatch.metadata)
    if policy_detail:
        metadata.update(policy_detail)

    rule = _build_match_rule(mismatch, form_type, matching_policy)

    return Evidence.from_mismatch(
        mismatch=mismatch,
        form_type=form_type,
        policy_detail=metadata,
    )


def create_candidate_from_mismatch(
    mismatch: EntityMismatch,
    entity_id: str,
    source_chunk: str,
    matching_policy: Optional[FormAwareMatchingPolicy] = None,
) -> ReviewCandidate:
    """Create a ReviewCandidate from an EntityMismatch.
    
    This is the main factory function. It extracts all necessary information
    from the mismatch and creates a fully-formed ReviewCandidate with evidence.
    """
    form_type = _infer_form_type_from_source(mismatch.source, mismatch.entity_type, matching_policy)

    # Build evidence
    policy_detail = {
        "match_rule": _build_match_rule(mismatch, form_type, matching_policy),
        "knowledge_id": mismatch.knowledge_id,
    }
    if matching_policy:
        nf_type = _form_type_to_matching_policy(form_type)
        if nf_type:
            spec = matching_policy.get_spec(nf_type)
            if spec:
                policy_detail["allowed_patterns"] = list(spec.allowed_patterns)
                policy_detail["forbidden_patterns"] = list(spec.forbidden_patterns)
                policy_detail["requires_exact"] = spec.requires_exact

    evidence = _build_evidence(mismatch, form_type, matching_policy, policy_detail)

    # Generate deterministic candidate ID
    candidate_id = _generate_candidate_id(
        entity_id=entity_id,
        form_type=form_type,
        expected=mismatch.expected,
        actual=mismatch.found or "[MISSING]",
        rule=policy_detail["match_rule"],
        source_context=source_chunk[:100],  # First 100 chars as context
    )

    candidate = ReviewCandidate(
        candidate_id=candidate_id,
        entity_id=entity_id,
        entity_type=mismatch.entity_type,
        source_form=mismatch.source,
        form_type=form_type,
        expected_translation=mismatch.expected,
        actual_translation=mismatch.found or "[MISSING]",
        severity=mismatch.severity,
        match_status="MISMATCH",
        source_location=source_chunk,
        evidence=evidence,
        origin=CandidateOrigin.ENTITY_CONSISTENCY,
        status=ReviewStatus.OPEN,
        metadata=dict(mismatch.metadata),
    )

    return candidate


def create_candidates_from_mismatches(
    mismatches: List[EntityMismatch],
    entity_id_map: Dict[str, str],
    source_chunk: str,
    matching_policy: Optional[FormAwareMatchingPolicy] = None,
) -> List[ReviewCandidate]:
    """Create ReviewCandidates from a list of EntityMismatches.
    
    Args:
        mismatches: List of mismatches from consistency checker
        entity_id_map: Mapping from source form -> entity_id
        source_chunk: The translation text chunk being checked
        matching_policy: Optional form-aware matching policy
    
    Returns:
        List of ReviewCandidate instances
    """
    candidates = []
    for mismatch in mismatches:
        entity_id = entity_id_map.get(mismatch.source, mismatch.source)
        candidate = create_candidate_from_mismatch(
            mismatch=mismatch,
            entity_id=entity_id,
            source_chunk=source_chunk,
            matching_policy=matching_policy,
        )
        candidates.append(candidate)
    return candidates


__all__ = [
    "create_candidate_from_mismatch",
    "create_candidates_from_mismatches",
]