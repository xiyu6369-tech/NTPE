from __future__ import annotations

import os
import re
from typing import Any, Mapping

SEGMENT_RECOVERY_VERSION = "5.5.3.3"
_COMPLETENESS_CODES = {
    "EMPTY_OUTPUT",
    "TOO_SHORT",
    "PARAGRAPH_OMISSION_SUSPECTED",
    "SENTENCE_OMISSION_SUSPECTED",
}


def segment_recovery_enabled() -> bool:
    value = os.environ.get("NTPE_SEGMENT_COMPLETENESS_RECOVERY", "1").strip().lower()
    return value not in {"0", "false", "off", "no"}


def _canonical_code(issue: Mapping[str, Any]) -> str:
    code = str(issue.get("code") or issue.get("type") or "").strip().upper()
    return code[3:] if code.startswith("V5_") else code


def completeness_issue_codes(qa_report: Mapping[str, Any] | None) -> tuple[str, ...]:
    report = qa_report or {}
    unified = report.get("unified_quality_report") if isinstance(report, Mapping) else None
    issues = unified.get("merged_issues", []) if isinstance(unified, Mapping) else report.get("issues", [])
    found: list[str] = []
    for issue in issues or []:
        if not isinstance(issue, Mapping):
            continue
        code = _canonical_code(issue)
        severity = str(issue.get("severity") or "").lower()
        blocking = bool(issue.get("retry_required") or issue.get("retry_worthy")) or severity in {"critical", "high"}
        if blocking and code in _COMPLETENESS_CODES and code not in found:
            found.append(code)
    return tuple(found)


def should_use_segment_recovery(qa_report: Mapping[str, Any] | None, source_text: str) -> bool:
    return segment_recovery_enabled() and len(source_text.strip()) >= 360 and bool(completeness_issue_codes(qa_report))


def split_recovery_segments(source_text: str, target_chars: int | None = None) -> list[str]:
    """Split source conservatively on paragraph/sentence boundaries.

    The goal is provider reliability, not semantic alignment. No source text is
    discarded and concatenating the returned segments preserves the source order.
    """
    text = source_text.strip()
    if not text:
        return []
    configured = target_chars or int(os.environ.get("NTPE_SEGMENT_RECOVERY_CHARS", "280") or 280)
    target = max(180, min(420, configured))

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs or [text]:
        if len(paragraph) <= target:
            units.append(paragraph)
            continue
        sentences = [s.strip() for s in re.split(r"(?<=[。！？!?\.])\s*", paragraph) if s.strip()]
        if len(sentences) <= 1:
            for start in range(0, len(paragraph), target):
                units.append(paragraph[start:start + target].strip())
        else:
            current = ""
            for sentence in sentences:
                candidate = sentence if not current else current + sentence
                if current and len(candidate) > target:
                    units.append(current.strip())
                    current = sentence
                else:
                    current = candidate
            if current.strip():
                units.append(current.strip())

    segments: list[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else current + "\n\n" + unit
        if current and len(candidate) > target:
            segments.append(current.strip() + "\n")
            current = unit
        else:
            current = candidate
    if current.strip():
        segments.append(current.strip() + "\n")

    # Recovery is useful only when it actually reduces request size.
    return segments if len(segments) >= 2 else [text + "\n"]


def recovery_metadata(source_text: str, segments: list[str], issue_codes: tuple[str, ...]) -> dict[str, Any]:
    return {
        "version": SEGMENT_RECOVERY_VERSION,
        "enabled": True,
        "strategy": "source_segment_retranslation",
        "issue_codes": list(issue_codes),
        "source_chars": len(source_text),
        "segment_count": len(segments),
        "segment_chars": [len(s) for s in segments],
    }
