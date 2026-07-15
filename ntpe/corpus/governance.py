"""Public read-only corpus governance view."""

from __future__ import annotations

from .compatibility import corpus_input, governance_input
from .models import CorpusView


def manage(*, corpus: object, governance_record: object | None = None) -> CorpusView:
    cases, content_sha256, corpus_refs = corpus_input(corpus)
    governance, lifecycle, governance_refs = governance_input(governance_record)
    approved_translations = sum(row.approved_final_translation is not None for row in cases)
    approved_cases = approved_translations
    if governance is not None and hasattr(governance, "case_id") and getattr(governance, "case_id") not in {row.case_id for row in cases}:
        raise ValueError("governance record references an unknown corpus case")
    return CorpusView(
        cases=cases,
        approved_case_count=approved_cases,
        approved_translation_count=approved_translations,
        lifecycle_summary=lifecycle,
        governance_record=governance,
        content_sha256=content_sha256,
        source_references=corpus_refs + governance_refs,
    )

