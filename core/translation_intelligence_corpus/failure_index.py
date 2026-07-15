from __future__ import annotations

from typing import Any


def build_failure_case_index(
    failure_cases: list[dict[str, Any]], cases_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for failure in failure_cases:
        case = cases_by_id[failure["case_id"]]
        items.append(
            {
                "failure_case_id": failure["failure_case_id"],
                "case_id": failure["case_id"],
                "alignment_id": failure["alignment_id"],
                "evidence_id": failure["evidence_id"],
                "failure_category": failure["failure_category"],
                "failure_subcategory": failure["failure_subcategory"],
                "severity": failure["severity"],
                "blocking": failure["blocking"],
                "source_file": failure["source_file"],
                "translation_file": failure["translation_file"],
                "provider": case["provider"],
                "model": case["model"],
                "stage": case["stage"],
                "version": case["version"],
                "review_source": failure["review_source"],
                "root_cause_status": failure["root_cause_status"],
                "corrected_translation_status": failure[
                    "corrected_translation_status"
                ],
            }
        )
    return {"schema_version": "tic.batch4.failure-case-index.v1", "items": items}
