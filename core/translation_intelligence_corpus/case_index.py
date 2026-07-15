from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _group(cases: Iterable[dict[str, Any]], field: str) -> dict[str, list[str]]:
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    for case in cases:
        grouped[str(case[field])].append(case["case_id"])
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def build_case_index(cases_payload: dict[str, Any]) -> dict[str, Any]:
    cases = cases_payload["translation_cases"]
    return {
        "schema_version": "tic.batch2.case-index.v1",
        "index_type": "metadata_only",
        "full_text_search": False,
        "case_count": len(cases),
        "by_case_id": {case["case_id"]: index for index, case in enumerate(cases)},
        "by_corpus_id": _group(cases, "corpus_id"),
        "by_stage": _group(cases, "stage"),
        "by_provider": _group(cases, "provider"),
        "by_model": _group(cases, "model"),
        "by_translation_status": _group(cases, "translation_status"),
        "by_source_file": _group(cases, "source_file"),
    }
