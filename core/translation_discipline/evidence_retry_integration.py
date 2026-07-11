from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from core.translation_evidence import (
    ALIGNMENT_ENGINE_VERSION,
    ALIGNMENT_EVIDENCE_VERSION,
    SemanticAlignmentResult,
    TranslationEvidence,
    build_alignment_evidence,
    build_source_translation_alignment,
)

from .retry_evidence import canonical_issue_code, extract_retry_evidence

EVIDENCE_RETRY_INTEGRATION_VERSION = "6.0.0-stage11.3"

_OMISSION_CODES = frozenset({"PARAGRAPH_OMISSION_SUSPECTED", "SENTENCE_OMISSION_SUSPECTED"})
_DUPLICATE_CODES = frozenset({"SEMANTIC_DUPLICATE_PARAGRAPH", "DUPLICATE_PARAGRAPH"})
_LOCALIZED_CODES = frozenset({"LOCKED_TERM_MISSING", "HANGUL_RESIDUE"})
_TARGETABLE_CODES = _OMISSION_CODES | _DUPLICATE_CODES | _LOCALIZED_CODES


def _valid_range(start: Any, end: Any, length: int, *, allow_empty: bool = False) -> bool:
    if isinstance(start, bool) or isinstance(end, bool):
        return False
    if not isinstance(start, int) or not isinstance(end, int):
        return False
    if start < 0 or end < start or end > length:
        return False
    return allow_empty or end > start


def _index_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    result: list[int] = []
    for item in value:
        if isinstance(item, bool):
            continue
        try:
            number = int(item)
        except (TypeError, ValueError):
            continue
        if number >= 0 and number not in result:
            result.append(number)
    return tuple(result)


def _issue_indexes(issue: Mapping[str, Any], key: str) -> tuple[int, ...]:
    raw = issue.get("evidence") if isinstance(issue.get("evidence"), Mapping) else {}
    metadata = issue.get("metadata") if isinstance(issue.get("metadata"), Mapping) else {}
    return _index_tuple(raw.get(key) or metadata.get(key))


def _evidence_metadata(item: TranslationEvidence) -> dict[str, Any]:
    return {
        "source_start": item.source_start,
        "source_end": item.source_end,
        "translated_start": item.translated_start,
        "translated_end": item.translated_end,
        "paragraph_indexes": list(item.paragraph_indexes),
        "sentence_indexes": list(item.sentence_indexes),
        "source_evidence": item.source_evidence,
        "translated_evidence": item.translated_evidence,
        "confidence": item.confidence,
        "reliable": item.reliable,
        "evidence_source": "translation_evidence_alignment",
        "evidence_retry_integration_version": EVIDENCE_RETRY_INTEGRATION_VERSION,
        "alignment_engine_version": ALIGNMENT_ENGINE_VERSION,
        "alignment_evidence_version": ALIGNMENT_EVIDENCE_VERSION,
        **dict(item.metadata),
    }


def _select_omission_evidence(
    issue: Mapping[str, Any],
    evidence: Sequence[TranslationEvidence],
) -> TranslationEvidence | None:
    paragraph_indexes = set(_issue_indexes(issue, "paragraph_indexes"))
    candidates = [
        item for item in evidence
        if item.code == "UNALIGNED_SOURCE_PARAGRAPH"
        and item.reliable
        and item.translated_start == item.translated_end
    ]
    if paragraph_indexes:
        candidates = [item for item in candidates if paragraph_indexes.intersection(item.paragraph_indexes)]
    # Never guess between multiple possible omissions.
    return candidates[0] if len(candidates) == 1 else None


def _select_aligned_evidence(
    issue: Mapping[str, Any],
    evidence: Sequence[TranslationEvidence],
) -> TranslationEvidence | None:
    paragraph_indexes = set(_issue_indexes(issue, "paragraph_indexes"))
    sentence_indexes = set(_issue_indexes(issue, "sentence_indexes"))
    candidates: list[TranslationEvidence] = []
    if paragraph_indexes:
        candidates.extend(
            item for item in evidence
            if item.code == "PARAGRAPH_ALIGNMENT"
            and item.reliable
            and paragraph_indexes.intersection(item.paragraph_indexes)
        )
    if sentence_indexes:
        candidates.extend(
            item for item in evidence
            if item.code == "SENTENCE_ALIGNMENT"
            and item.reliable
            and sentence_indexes.intersection(item.sentence_indexes)
        )
    unique = {
        (item.source_start, item.source_end, item.translated_start, item.translated_end): item
        for item in candidates
    }
    return next(iter(unique.values())) if len(unique) == 1 else None


def _select_translated_range_evidence(
    issue: Mapping[str, Any],
    evidence: Sequence[TranslationEvidence],
    translated_length: int,
) -> TranslationEvidence | None:
    raw = issue.get("evidence") if isinstance(issue.get("evidence"), Mapping) else {}
    metadata = issue.get("metadata") if isinstance(issue.get("metadata"), Mapping) else {}
    start = raw.get("translated_start", metadata.get("translated_start"))
    end = raw.get("translated_end", metadata.get("translated_end"))
    if not _valid_range(start, end, translated_length):
        return _select_aligned_evidence(issue, evidence)
    candidates = [
        item for item in evidence
        if item.reliable
        and item.translated_start is not None
        and item.translated_end is not None
        and item.translated_start <= start
        and item.translated_end >= end
        and item.source_start is not None
        and item.source_end is not None
    ]
    return candidates[0] if len(candidates) == 1 else None


@dataclass(frozen=True)
class EvidenceRetryIntegrationResult:
    report: dict[str, Any]
    alignment: SemanticAlignmentResult
    evidence: tuple[TranslationEvidence, ...]
    applied_issue_codes: tuple[str, ...] = ()
    skipped_issue_codes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": EVIDENCE_RETRY_INTEGRATION_VERSION,
            "alignment_engine_version": ALIGNMENT_ENGINE_VERSION,
            "alignment_evidence_version": ALIGNMENT_EVIDENCE_VERSION,
            "alignment_reliable": self.alignment.reliable,
            "alignment_confidence": self.alignment.confidence,
            "evidence_count": len(self.evidence),
            "reliable_evidence_count": sum(1 for item in self.evidence if item.reliable),
            "applied_issue_codes": list(self.applied_issue_codes),
            "skipped_issue_codes": list(self.skipped_issue_codes),
            "runtime_integrated": True,
            "fail_closed": True,
            **dict(self.metadata),
        }


def integrate_alignment_evidence_for_retry(
    unified_report: Mapping[str, Any] | None,
    *,
    source_text: str,
    translated_text: str,
    alignment: SemanticAlignmentResult | None = None,
    evidence: Sequence[TranslationEvidence] | None = None,
) -> EvidenceRetryIntegrationResult:
    """Enrich targetable issues with reliable alignment evidence.

    Existing explicit reliable evidence is never replaced. Alignment evidence is
    applied only when one unique, bounded mapping exists. Otherwise the report is
    returned unchanged so Stage 10 remains fail-closed and uses full retry.
    """
    report = deepcopy(dict(unified_report or {}))
    alignment_result = alignment or build_source_translation_alignment(source_text, translated_text)
    alignment_evidence = tuple(evidence or build_alignment_evidence(source_text, translated_text, alignment_result))
    issues = report.get("merged_issues") or []
    applied: list[str] = []
    skipped: list[str] = []

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        code = canonical_issue_code(issue.get("code") or issue.get("type"))
        if code not in _TARGETABLE_CODES:
            continue
        explicit = extract_retry_evidence(issue, source_text)
        if explicit.reliable and explicit.has_source_range:
            skipped.append(code)
            continue

        selected: TranslationEvidence | None = None
        if code in _OMISSION_CODES:
            selected = _select_omission_evidence(issue, alignment_evidence)
        elif code in _DUPLICATE_CODES:
            selected = _select_aligned_evidence(issue, alignment_evidence)
        elif code in _LOCALIZED_CODES:
            selected = _select_translated_range_evidence(issue, alignment_evidence, len(translated_text))

        if selected is None or not selected.reliable:
            skipped.append(code)
            continue
        if not _valid_range(selected.source_start, selected.source_end, len(source_text)):
            skipped.append(code)
            continue
        if not _valid_range(
            selected.translated_start,
            selected.translated_end,
            len(translated_text),
            allow_empty=code in _OMISSION_CODES,
        ):
            skipped.append(code)
            continue

        issue["evidence"] = _evidence_metadata(selected)
        issue_metadata = dict(issue.get("metadata") or {})
        issue_metadata.update({
            "evidence_retry_integrated": True,
            "evidence_retry_integration_version": EVIDENCE_RETRY_INTEGRATION_VERSION,
            "evidence_retry_detector": selected.detector,
        })
        issue["metadata"] = issue_metadata
        applied.append(code)

    metadata = {
        "targetable_issue_count": sum(
            1 for issue in issues
            if isinstance(issue, Mapping)
            and canonical_issue_code(issue.get("code") or issue.get("type")) in _TARGETABLE_CODES
        ),
    }
    result = EvidenceRetryIntegrationResult(
        report=report,
        alignment=alignment_result,
        evidence=alignment_evidence,
        applied_issue_codes=tuple(sorted(set(applied))),
        skipped_issue_codes=tuple(sorted(set(skipped))),
        metadata=metadata,
    )
    report["evidence_retry_integration"] = result.to_metadata()
    return result
