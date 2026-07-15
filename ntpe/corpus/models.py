"""Immutable, non-serialized corpus views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from core.translation_quality_corpus import GoldenReviewCase
from core.translation_quality_corpus_governance import CorpusGovernanceRecord


@dataclass(frozen=True, slots=True)
class CorpusView:
    cases: tuple[GoldenReviewCase, ...]
    approved_case_count: int
    approved_translation_count: int
    lifecycle_summary: tuple[tuple[str, int], ...]
    governance_record: CorpusGovernanceRecord | Mapping[str, object] | None
    content_sha256: str
    source_references: tuple[str, ...]

