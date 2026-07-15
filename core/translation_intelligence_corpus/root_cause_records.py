"""Evidence-bounded root-cause records for the two TIC Batch 6 cases."""

from __future__ import annotations

from typing import Any

from core.shared.evidence import canonical_json_bytes, sha256_bytes

from .correction_records import BATCH5_CORPUS, with_integrity


def _root_cause_id(failure: dict[str, Any], primary: str) -> str:
    identity = {
        "failure_case_id": failure["failure_case_id"],
        "failure_category": failure["failure_category"],
        "primary_root_cause": primary,
    }
    return "TIC-ROOT-B6-" + sha256_bytes(canonical_json_bytes(identity))[:20].upper()


def _subject_shift_record(failure: dict[str, Any]) -> dict[str, Any]:
    primary = "offline_qa_did_not_detect_the_observed_semantic_actor_shift"
    return with_integrity(
        {
            "schema_version": "tic.batch6.root-cause-record.v1",
            "root_cause_id": _root_cause_id(failure, primary),
            "failure_case_id": failure["failure_case_id"],
            "failure_category": failure["failure_category"],
            "root_cause_status": "evidence_supported",
            "primary_root_cause": primary,
            "secondary_root_causes": [
                {
                    "cause": "long_distance_subject_resolution_risk",
                    "status": "evidence_supported",
                },
                {
                    "cause": "prompt_subject_preservation_rule_may_be_insufficient",
                    "status": "insufficient_evidence",
                },
            ],
            "evidence": {
                "observed": failure["observed_error"],
                "semantic_constraint": failure["expected_semantic_constraint"],
                "layer_assessment": {
                    "prompt": "insufficient_evidence; prompt was not modified or causally tested",
                    "context": "source contains a distant antecedent followed by 그는",
                    "model_output": "observed translation binds understanding to 鄭泰義",
                    "post_processing": "insufficient_evidence; no transformation was attributed",
                    "QA_detection": "human review found a semantic actor shift not previously guarded",
                },
            },
            "confidence": "high",
            "human_review_required": True,
            "affected_layer": "QA detection",
            "recommended_fix_location": "semantic regression",
            "fix_scope": "one case-bound required-semantic-actor regression",
            "non_fix_locations": [
                "runtime",
                "provider",
                "post-processing",
                "global translation strategy",
            ],
            "quality_risk": "high",
            "runtime_risk": "none_until_a_production_fix_is_proposed",
            "performance_risk": "none_for_offline_regression",
            "source_references": [BATCH5_CORPUS, *failure["source_references"]],
        }
    )


def _lexical_record(failure: dict[str, Any]) -> dict[str, Any]:
    primary = "contextual_lexical_disambiguation_failed_in_the_observed_output"
    return with_integrity(
        {
            "schema_version": "tic.batch6.root-cause-record.v1",
            "root_cause_id": _root_cause_id(failure, primary),
            "failure_case_id": failure["failure_case_id"],
            "failure_category": failure["failure_category"],
            "root_cause_status": "evidence_supported",
            "primary_root_cause": primary,
            "secondary_root_causes": [
                {
                    "cause": "korean_chinese_near_form_lexical_selection_risk",
                    "status": "evidence_supported",
                },
                {
                    "cause": "traditional_chinese_lexical_validation_gap",
                    "status": "evidence_supported",
                },
            ],
            "evidence": {
                "observed": failure["observed_error"],
                "semantic_constraint": failure["expected_semantic_constraint"],
                "layer_assessment": {
                    "prompt": "insufficient_evidence; prompt was not modified or causally tested",
                    "context": "인간 denotes a rational person in the frozen local context",
                    "model_output": "the observed wording uses 人間 for a person",
                    "post_processing": "insufficient_evidence; no transformation was attributed",
                    "QA_detection": "the invalid local lexical choice lacked a fixed-case guard",
                },
            },
            "confidence": "high",
            "human_review_required": True,
            "affected_layer": "model output and QA detection",
            "recommended_fix_location": "lexical validator",
            "fix_scope": "one fixed-case forbidden-phrase and human-person allowlist check",
            "non_fix_locations": [
                "runtime",
                "provider",
                "global string replacement",
                "global glossary",
            ],
            "quality_risk": "medium",
            "runtime_risk": "none_until_a_production_fix_is_proposed",
            "performance_risk": "none_for_offline_regression",
            "source_references": [BATCH5_CORPUS, *failure["source_references"]],
        }
    )


def build_root_cause_records(failures: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for failure in failures:
        category = failure["failure_category"]
        if category == "subject_reference_shift":
            records.append(_subject_shift_record(failure))
        elif category == "lexical_choice":
            records.append(_lexical_record(failure))
        else:
            raise ValueError(f"unsupported Batch 6 failure category: {category}")
    return {
        "schema_version": "tic.batch6.root-cause-records.v1",
        "items": records,
    }
