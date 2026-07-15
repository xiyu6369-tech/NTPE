from __future__ import annotations

from collections import Counter
from typing import Any


def _counts(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter("null" if value is None else str(value) for value in values).items()))


def build_failure_statistics(
    failure_cases: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    cases_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_metadata = [cases_by_id[item["case_id"]] for item in failure_cases]
    return {
        "schema_version": "tic.batch4.failure-corpus-statistics.v1",
        "total_failure_cases": len(failure_cases),
        "failure_category_counts": _counts(
            [item["failure_category"] for item in failure_cases]
        ),
        "failure_subcategory_counts": _counts(
            [item["failure_subcategory"] for item in failure_cases]
        ),
        "severity_counts": _counts([item["severity"] for item in failure_cases]),
        "blocking_count": sum(item["blocking"] is True for item in failure_cases),
        "nonblocking_count": sum(item["blocking"] is False for item in failure_cases),
        "human_evidence_count": sum(
            item["reviewer_type"] == "human" for item in evidence_items
        ),
        "automatic_evidence_excluded_count": sum(
            item["reviewer_type"] == "automatic" for item in evidence_items
        ),
        "unknown_evidence_excluded_count": sum(
            item["reviewer_type"] == "unknown" for item in evidence_items
        ),
        "precisely_aligned_failure_count": len(failure_cases),
        "linked_but_not_aligned_count": sum(
            item["current_status"] == "linked_but_not_aligned" for item in excluded
        ),
        "excluded_candidate_count": len(excluded),
        "root_cause_analyzed_count": sum(
            item["root_cause_status"] == "human_confirmed" for item in failure_cases
        ),
        "root_cause_pending_count": sum(
            item["root_cause_status"] != "human_confirmed" for item in failure_cases
        ),
        "corrected_translation_available_count": sum(
            item["corrected_translation_status"] == "provided" for item in failure_cases
        ),
        "corrected_translation_missing_count": sum(
            item["corrected_translation_status"] != "provided" for item in failure_cases
        ),
        "source_files_count": len({item["source_file"] for item in failure_cases}),
        "translation_files_count": len(
            {item["translation_file"] for item in failure_cases}
        ),
        "providers": sorted({item["provider"] for item in case_metadata}),
        "models": sorted({item["model"] for item in case_metadata}),
        "stages": sorted({item["stage"] for item in case_metadata}),
        "versions": sorted({item["version"] for item in case_metadata}),
    }
