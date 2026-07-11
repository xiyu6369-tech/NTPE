from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


_SEVERITY_ALIASES = {
    "fatal": "critical",
    "error": "high",
    "warning": "medium",
    "warn": "medium",
}

_CANONICAL_CODES = {
    "EMPTY_TRANSLATION": "EMPTY_OUTPUT",
    "EMPTY_OUTPUT": "EMPTY_OUTPUT",
    "LENGTH_RATIO_TOO_LOW": "TOO_SHORT",
    "TOO_SHORT": "TOO_SHORT",
    "KOREAN_RESIDUE": "HANGUL_RESIDUE",
    "HANGUL_RESIDUE": "HANGUL_RESIDUE",
    "REPEATED_LINES": "DUPLICATE_LINE",
    "DUPLICATE_LINE": "DUPLICATE_LINE",
    "REPEATED_SENTENCES": "DUPLICATE_SENTENCE",
    "DUPLICATE_PARAGRAPH": "DUPLICATE_PARAGRAPH",
    "LOCKED_TERM_VIOLATION": "LOCKED_TERM_MISSING",
    "LOCKED_TERM_MISSING": "LOCKED_TERM_MISSING",
    "DIALOGUE_QUOTE_FORMAT": "DIALOGUE_QUOTE_FORMAT",
}

_CATEGORIES = {
    "EMPTY_OUTPUT": "completeness",
    "TOO_SHORT": "completeness",
    "TOO_LONG": "completeness",
    "PARAGRAPH_OMISSION_SUSPECTED": "completeness",
    "SENTENCE_OMISSION_SUSPECTED": "completeness",
    "HANGUL_RESIDUE": "language_residue",
    "DUPLICATE_LINE": "repetition",
    "DUPLICATE_SENTENCE": "repetition",
    "DUPLICATE_PARAGRAPH": "repetition",
    "LOCKED_TERM_MISSING": "terminology",
    "LOCKED_ALIAS_USED": "terminology",
    "DIALOGUE_QUOTE_FORMAT": "formatting",
    "SIMPLIFIED_CHINESE": "orthography",
    "NATURALNESS_GUARD": "naturalness",
    "QUALITY_LOCK_VIOLATION": "semantic_guard",
    "HALLUCINATION": "hallucination",
    "ADDED_DETAIL": "hallucination",
}


def normalize_severity(value: Any, *, default: str = "medium") -> str:
    severity = str(value or default).strip().lower()
    severity = _SEVERITY_ALIASES.get(severity, severity)
    if severity not in {"critical", "high", "medium", "low", "info"}:
        return default
    return severity


def canonical_issue_code(value: Any) -> str:
    code = str(value or "QUALITY_ISSUE").strip().upper()
    if code.startswith("V5_"):
        code = code[3:]
    return _CANONICAL_CODES.get(code, code)


def category_for_code(code: str) -> str:
    return _CATEGORIES.get(canonical_issue_code(code), "quality")


@dataclass(frozen=True)
class UnifiedQualityIssue:
    code: str
    category: str
    severity: str
    message: str
    evidence: Any = field(default_factory=dict)
    source: str = "unknown"
    repairable: bool = False
    retry_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def quality_v5_issue_to_unified(
    issue: Mapping[str, Any],
    *,
    report_retry_required: bool = False,
) -> UnifiedQualityIssue:
    code = canonical_issue_code(issue.get("code"))
    severity = normalize_severity(issue.get("severity"), default="medium")
    repair_action = str(issue.get("repair_action") or "")
    metadata = dict(issue.get("metadata") or issue.get("details") or {})
    metadata["original_code"] = str(issue.get("code") or "")
    if repair_action:
        metadata["repair_action"] = repair_action
    evidence = issue.get("evidence")
    if evidence is None:
        evidence = issue.get("samples", metadata)
    repairable = repair_action in {
        "apply_locked_terminology",
        "full_traditional_chinese_conversion",
        "normalize_dialogue_quotes",
    }

    # TE v5.3.1.2: report-level retry is an aggregate outcome and must not
    # be copied onto every detailed issue. Doing so turns unrelated medium
    # warnings into blocking retries. Detailed issues decide retry from their
    # own severity/flag; the unified gate already creates a synthetic blocking
    # issue when a rejected report contains no detailed issues.
    nonblocking_codes = {
        "PARAGRAPH_STRUCTURE_MERGED",
    }
    explicit_retry = bool(issue.get("retry_required"))

    # Deterministic normalization issues must be reported, but provider retry
    # is not the repair mechanism. Under the normalize policy they remain a
    # warning and are handled by the local normalization pipeline.
    if code == "SIMPLIFIED_CHINESE" and repairable:
        severity = "medium"
        explicit_retry = False

    if code in nonblocking_codes:
        severity = "medium"
        explicit_retry = False

    return UnifiedQualityIssue(
        code=code,
        category=category_for_code(code),
        severity=severity,
        message=str(issue.get("message") or code),
        evidence=evidence,
        source="translation_quality_v5",
        repairable=repairable,
        retry_required=explicit_retry or severity in {"critical", "high"},
        metadata=metadata,
    )
