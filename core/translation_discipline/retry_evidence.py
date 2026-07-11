from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

RETRY_EVIDENCE_VERSION = "6.0.0-stage10"


def canonical_issue_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    return code[3:] if code.startswith("V5_") else code


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _indexes(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(dict.fromkeys(item for raw in value if (item := _optional_int(raw)) is not None))


@dataclass(frozen=True)
class RetryEvidence:
    issue_code: str
    source: str = ""
    source_start: int | None = None
    source_end: int | None = None
    paragraph_indexes: tuple[int, ...] = ()
    sentence_indexes: tuple[int, ...] = ()
    translated_evidence: str = ""
    source_evidence: str = ""
    confidence: float = 0.0
    reliable: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "issue_code", canonical_issue_code(self.issue_code))
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence or 0.0))))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def has_source_range(self) -> bool:
        return self.source_start is not None and self.source_end is not None and self.source_end > self.source_start

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": RETRY_EVIDENCE_VERSION,
            "issue_code": self.issue_code,
            "source": self.source,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "paragraph_indexes": list(self.paragraph_indexes),
            "sentence_indexes": list(self.sentence_indexes),
            "translated_evidence": self.translated_evidence,
            "source_evidence": self.source_evidence,
            "confidence": self.confidence,
            "reliable": self.reliable,
            "metadata": dict(self.metadata),
        }


def extract_retry_evidence(issue: Mapping[str, Any], source_text: str = "") -> RetryEvidence:
    metadata = dict(issue.get("metadata") or {})
    raw = issue.get("evidence")
    evidence = dict(raw) if isinstance(raw, Mapping) else {}
    evidence.update({key: value for key, value in metadata.items() if key not in evidence})
    start = _optional_int(evidence.get("source_start"))
    end = _optional_int(evidence.get("source_end"))
    in_bounds = start is not None and end is not None and start < end <= len(source_text)
    source_evidence = str(evidence.get("source_evidence") or "")
    if in_bounds and not source_evidence:
        source_evidence = source_text[start:end]
    confidence = float(evidence.get("confidence") or 0.0)
    declared_reliable = evidence.get("reliable") is True
    # Never infer offsets from similarity or snippets. Reliable targeting needs
    # an explicit, in-bounds source range and an affirmative reliability flag.
    reliable = bool(declared_reliable and in_bounds and confidence >= 0.70)
    excluded = {
        "source_start", "source_end", "paragraph_indexes", "sentence_indexes",
        "translated_evidence", "source_evidence", "confidence", "reliable",
    }
    return RetryEvidence(
        issue_code=canonical_issue_code(issue.get("code") or issue.get("type")),
        source=str(issue.get("source") or ""),
        source_start=start,
        source_end=end,
        paragraph_indexes=_indexes(evidence.get("paragraph_indexes")),
        sentence_indexes=_indexes(evidence.get("sentence_indexes")),
        translated_evidence=str(evidence.get("translated_evidence") or ""),
        source_evidence=source_evidence,
        confidence=confidence,
        reliable=reliable,
        metadata={key: value for key, value in evidence.items() if key not in excluded},
    )


def collect_retry_evidence(report: Mapping[str, Any], source_text: str = "") -> tuple[RetryEvidence, ...]:
    return tuple(
        extract_retry_evidence(issue, source_text)
        for issue in report.get("merged_issues") or ()
        if isinstance(issue, Mapping)
    )
