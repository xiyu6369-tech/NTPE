from __future__ import annotations

from collections import Counter
from typing import Any


def _average(values: list[int]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def build_case_statistics(
    cases_payload: dict[str, Any], *, inventory_count: int
) -> dict[str, Any]:
    cases = cases_payload["translation_cases"]
    reviewed = sum(case["has_manual_review"] for case in cases)
    completed = sum(
        case["translation_status"] in {"Completed Translation", "Manual Reviewed"}
        for case in cases
    )
    partial = sum("Partial Translation" in case["status_tags"] for case in cases)
    coverage = round(len(cases) / inventory_count * 100.0, 2) if inventory_count else 0.0
    sources = Counter(case["source_file"] for case in cases)
    return {
        "schema_version": "tic.batch2.case-statistics.v1",
        "total_translation_cases": len(cases),
        "completed_cases": completed,
        "partial_cases": partial,
        "cases_with_review": reviewed,
        "cases_without_review": len(cases) - reviewed,
        "average_chunk_size": _average([len(case["source_text"]) for case in cases]),
        "average_translation_length": _average(
            [len(case["translation_text"]) for case in cases]
        ),
        "corpus_coverage": {
            "case_numerator": len(cases),
            "inventory_denominator": inventory_count,
            "percent": coverage,
        },
        "translation_sources": dict(sorted(sources.items())),
        "execution_evidence_only": len(cases_payload["execution_evidence"]),
        "excluded_without_case_or_execution": cases_payload[
            "excluded_without_case_or_execution"
        ],
    }
