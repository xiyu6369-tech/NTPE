from __future__ import annotations

from dataclasses import asdict

from .models import ExtractedSemanticFeatures, SemanticDifference, SemanticInvariant
from .policy import SemanticVerificationPolicy
from .validation import sha256_text

FIELDS = {
    "names": "named_entity", "numbers": "number", "times": "time_expression",
    "negations": "negation", "modalities": "modality", "causal_markers": "causal_relation",
    "order_markers": "event_order", "dialogue_spans": "dialogue_boundary",
    "paragraphs": "paragraph_boundary", "glossary_terms": "glossary_term",
    "ambiguity_markers": "ambiguity_preservation", "source_language_residue": "source_language_residue",
    "target_script_consistent": "target_script_consistency",
}


def _norm_number(value: str) -> str:
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value and value[0] in digits and value[0] != "零":
        suffix = value[1:]
        if not suffix or suffix[0] in "天日年月歲次個人點分秒%％": return str(digits[value[0]]) + suffix
    return value.replace("％", "%")


def compare_semantic_features(draft: ExtractedSemanticFeatures, polish: ExtractedSemanticFeatures, *, invariants: tuple[SemanticInvariant, ...] = (), policy: SemanticVerificationPolicy) -> tuple[SemanticDifference, ...]:
    differences = []
    approved = {x.invariant_type: x.expected_value for x in invariants if x.approval_status == "human_approved"}
    for field, kind in FIELDS.items():
        old, new = getattr(draft, field), getattr(polish, field)
        if field == "numbers": old, new = tuple(map(_norm_number, old)), tuple(map(_norm_number, new))
        if field == "paragraphs" and policy.allowed_punctuation_changes:
            strip = lambda values: tuple("".join(ch for ch in x if ch not in "，。！？；：、,.!?;:\"'「」『』") for x in values)
            old, new = strip(old), strip(new)
        if old == new or (kind in approved and new == approved[kind]): continue
        difference_type = "ambiguity_loss" if kind == "ambiguity_preservation" and len(new) < len(old) else kind
        if kind == "named_entity" and any(a in b and len(b) > len(a) for a in old for b in new): difference_type = "name_completion"
        severity = "critical" if difference_type in policy.critical_issue_types else "blocking" if difference_type in policy.blocking_issue_types else "review"
        evidence = {"feature": field, "draft": old, "polish": new}
        differences.append(SemanticDifference("diff-" + sha256_text(repr(evidence))[:16], difference_type, None, old, new, "full_chunk", evidence, 1.0, severity, difference_type in policy.blocking_issue_types))
    for item in invariants:
        if item.invariant_type in FIELDS.values(): continue
        observed = approved.get(item.invariant_type, item.expected_value)
        if isinstance(observed, dict) and "polish_value" in observed and observed["polish_value"] != observed.get("expected_value"):
            differences.append(SemanticDifference("diff-" + item.invariant_id, item.invariant_type, item.source_evidence, item.draft_evidence, observed["polish_value"], item.scope, {"invariant_id": item.invariant_id}, item.confidence, "blocking", item.blocking))
    return tuple(sorted(differences, key=lambda x: (x.difference_type, x.difference_id)))
