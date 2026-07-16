from __future__ import annotations

from dataclasses import asdict
from typing import Mapping

from .comparison import compare_semantic_features
from .evidence import build_evidence
from .extraction import extract_semantic_features
from .invariants import invariant_fingerprint
from .models import *
from .policy import DEFAULT_POLICY, get_policy
from .serialization import canonical_json
from .validation import sha256_text, validate_input, validate_invariant


def create_verification_input(**values) -> SemanticVerificationInput:
    values = dict(values)
    for text, digest in (("source_text", "source_hash"), ("verified_draft_text", "verified_draft_hash"), ("polish_text", "polish_hash")):
        values.setdefault(digest, sha256_text(values.get(text, "")))
    item = SemanticVerificationInput(**values)
    return item


def _empty_evidence() -> SemanticVerificationEvidence:
    empty = sha256_text("")
    return SemanticVerificationEvidence(empty, empty, empty)


def _result(status, decision, item, *, issues=(), checked=(), unverifiable=(), explanation="", evidence=None):
    payload = {"status": status.value, "decision": decision.value, "issues": [asdict(x) for x in issues], "checked": checked, "unverifiable": unverifiable, "policy": item.semantic_policy_version, "source": item.source_hash, "draft": item.verified_draft_hash, "polish": item.polish_hash}
    return SemanticVerificationResult(status, decision, tuple(issues), tuple(checked), tuple(unverifiable), item.semantic_policy_version, item.source_hash, item.verified_draft_hash, item.polish_hash, sha256_text(canonical_json(payload)), explanation, evidence or _empty_evidence())


def verify_post_polish_semantics(item: SemanticVerificationInput, *, invariants: tuple[SemanticInvariant, ...] = (), glossary: Mapping[str, str] | None = None, policy: SemanticVerificationPolicy | None = None) -> SemanticVerificationResult:
    try:
        validate_input(item)
        selected_policy = policy or get_policy(item.semantic_policy_id, item.semantic_policy_version)
        for inv in invariants: validate_invariant(inv)
    except (TypeError, ValueError) as exc:
        issue = SemanticIssue("input-invalid", "invalid_input", "blocking", str(exc), {}, True)
        return _result(VerificationStatus.INVALID_INPUT, VerificationDecision.BLOCK_OUTPUT, item, issues=(issue,), explanation="Input or policy validation failed closed.")
    conflicts = [x for x in invariants if x.approval_status == "conflicting"]
    if conflicts:
        issue = SemanticIssue("approved-evidence-conflict", "conflicting_human_approved_evidence", "blocking", "Conflicting approved evidence cannot be resolved offline.", {"ids": [x.invariant_id for x in conflicts]}, True)
        return _result(VerificationStatus.CONFLICT, VerificationDecision.BLOCK_OUTPUT, item, issues=(issue,), explanation="Conflicting approved evidence.")
    draft = extract_semantic_features(item.verified_draft_text, glossary=glossary)
    polish = extract_semantic_features(item.polish_text, glossary=glossary)
    differences = compare_semantic_features(draft, polish, invariants=invariants, policy=selected_policy)
    inv_fp = invariant_fingerprint(invariants)
    evidence = build_evidence(draft, polish, differences, inv_fp)
    issues = tuple(SemanticIssue(x.difference_id, x.difference_type, x.severity, f"Protected {x.difference_type} changed.", x.evidence, x.blocking) for x in differences)
    checked = tuple(sorted(set(selected_policy.required_invariants) | {x.invariant_type for x in invariants}))
    explicit = {x.invariant_type for x in invariants}
    structural = {"number", "time_expression", "negation", "modality", "causal_relation", "dialogue_boundary", "paragraph_boundary", "ambiguity_preservation", "scope_integrity"}
    unverifiable = tuple(sorted(x for x in ("subject_identity", "pronoun_reference", "relationship", "speaker", "point_of_view", "event_presence", "action_agent", "action_patient") if x not in explicit))
    if any(x.blocking for x in issues):
        return _result(VerificationStatus.FAILED, VerificationDecision.ROLLBACK_TO_DRAFT, item, issues=issues, checked=checked, unverifiable=unverifiable, explanation="One or more protected semantic invariants changed; rollback is required.", evidence=evidence)
    if len(checked) < selected_policy.minimum_evidence or not structural <= set(checked):
        return _result(VerificationStatus.INSUFFICIENT_EVIDENCE, VerificationDecision.MANUAL_REVIEW_REQUIRED, item, checked=checked, unverifiable=unverifiable, explanation="Minimum independent evidence was not available.", evidence=evidence)
    if unverifiable and invariants:
        # Provided invariants are authoritative only for the fields they explicitly cover.
        pass
    return _result(VerificationStatus.PASSED, VerificationDecision.ACCEPT_POLISH, item, checked=checked, unverifiable=unverifiable, explanation="All available fixed structural invariants passed; this is not general semantic understanding.", evidence=evidence)


def build_verification_identity(item: SemanticVerificationInput, *, invariant_fingerprint_value: str, scope_hash: str | None = None) -> str:
    identity = {"source_hash": item.source_hash, "draft_hash": item.verified_draft_hash, "polish_hash": item.polish_hash, "semantic_policy_version": item.semantic_policy_version, "glossary_fingerprint": item.glossary_fingerprint, "character_memory_fingerprint": item.character_memory_fingerprint, "context_scene_fingerprint": item.context_scene_fingerprint, "scope_hash": scope_hash or sha256_text(canonical_json(item.polish_scope)), "invariant_fingerprint": invariant_fingerprint_value}
    return sha256_text(canonical_json(identity))
