# =====================================================
# NTPE 1.2 Professional
# Stage-15.2 Translation Completeness / Missing Segment Detection
# =====================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?\.])\s+|(?<=[。！？!?\.])")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")


@dataclass(frozen=True)
class CompletenessSegment:
    """A deterministic source/target alignment unit used by Stage-15.2."""

    index: int
    source: str = ""
    translated: str = ""
    source_length: int = 0
    translated_length: int = 0
    length_ratio: float = 1.0
    status: str = "ok"
    severity: str = "info"
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "source_length": self.source_length,
            "translated_length": self.translated_length,
            "length_ratio": round(float(self.length_ratio), 4),
            "status": self.status,
            "severity": self.severity,
            "reason": self.reason,
            "source_preview": self.source[:160],
            "translated_preview": self.translated[:160],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CompletenessAnalysis:
    source_segments: int
    translated_segments: int
    aligned_segments: List[CompletenessSegment]
    missing_segments: List[CompletenessSegment]
    short_segments: List[CompletenessSegment]
    extra_segments: List[CompletenessSegment]
    metrics: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not self.missing_segments and not any(s.severity == "error" for s in self.short_segments)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "source_segments": self.source_segments,
            "translated_segments": self.translated_segments,
            "missing_segments": [s.to_dict() for s in self.missing_segments],
            "short_segments": [s.to_dict() for s in self.short_segments],
            "extra_segments": [s.to_dict() for s in self.extra_segments],
            "aligned_segments": [s.to_dict() for s in self.aligned_segments],
            "metrics": dict(self.metrics),
        }


class TranslationCompletenessAnalyzer:
    """Static missing-segment detector for translated novel text.

    Stage-15.2 intentionally avoids AI calls. It detects likely omissions by
    aligning source and translation paragraphs/sentences and applying stable
    length/structure thresholds. This makes it safe for regression tests,
    provider-independent runtime checks, and offline quality reports.
    """

    def __init__(
        self,
        *,
        min_segment_ratio: float = 0.20,
        warning_segment_ratio: float = 0.45,
        min_total_ratio: float = 0.15,
    ) -> None:
        self.min_segment_ratio = min_segment_ratio
        self.warning_segment_ratio = warning_segment_ratio
        self.min_total_ratio = min_total_ratio

    def analyze(self, source_text: str, translated_text: str) -> CompletenessAnalysis:
        source_units = self._split_units(source_text)
        translated_units = self._split_units(translated_text)
        max_len = max(len(source_units), len(translated_units))

        aligned: List[CompletenessSegment] = []
        missing: List[CompletenessSegment] = []
        short: List[CompletenessSegment] = []
        extra: List[CompletenessSegment] = []

        for idx in range(max_len):
            src = source_units[idx] if idx < len(source_units) else ""
            dst = translated_units[idx] if idx < len(translated_units) else ""
            seg = self._classify(idx + 1, src, dst)
            aligned.append(seg)
            if seg.status == "missing":
                missing.append(seg)
            elif seg.status in {"too_short", "possibly_short"}:
                short.append(seg)
            elif seg.status == "extra_translation":
                extra.append(seg)

        source_length = len((source_text or "").strip())
        translated_length = len((translated_text or "").strip())
        total_ratio = translated_length / max(1, source_length) if source_length else 1.0
        coverage_ratio = (len(source_units) - len(missing)) / max(1, len(source_units)) if source_units else 1.0

        metrics = {
            "source_length": source_length,
            "translated_length": translated_length,
            "total_length_ratio": round(float(total_ratio), 4),
            "segment_coverage_ratio": round(float(coverage_ratio), 4),
            "missing_count": len(missing),
            "short_count": len(short),
            "extra_count": len(extra),
            "min_segment_ratio": self.min_segment_ratio,
            "warning_segment_ratio": self.warning_segment_ratio,
            "min_total_ratio": self.min_total_ratio,
        }
        return CompletenessAnalysis(
            source_segments=len(source_units),
            translated_segments=len(translated_units),
            aligned_segments=aligned,
            missing_segments=missing,
            short_segments=short,
            extra_segments=extra,
            metrics=metrics,
        )

    def _classify(self, index: int, source: str, translated: str) -> CompletenessSegment:
        source = (source or "").strip()
        translated = (translated or "").strip()
        src_len = len(source)
        dst_len = len(translated)
        ratio = dst_len / max(1, src_len) if src_len else 1.0

        if source and not translated:
            return CompletenessSegment(
                index=index,
                source=source,
                translated=translated,
                source_length=src_len,
                translated_length=dst_len,
                length_ratio=0.0,
                status="missing",
                severity="error",
                reason="source segment has no corresponding translation",
            )
        if not source and translated:
            return CompletenessSegment(
                index=index,
                source=source,
                translated=translated,
                source_length=src_len,
                translated_length=dst_len,
                length_ratio=1.0,
                status="extra_translation",
                severity="info",
                reason="translation contains an extra segment without source counterpart",
            )
        if src_len >= 40 and ratio < self.min_segment_ratio:
            return CompletenessSegment(
                index=index,
                source=source,
                translated=translated,
                source_length=src_len,
                translated_length=dst_len,
                length_ratio=ratio,
                status="too_short",
                severity="error",
                reason="translated segment is below minimum completeness ratio",
            )
        if src_len >= 40 and ratio < self.warning_segment_ratio:
            return CompletenessSegment(
                index=index,
                source=source,
                translated=translated,
                source_length=src_len,
                translated_length=dst_len,
                length_ratio=ratio,
                status="possibly_short",
                severity="warning",
                reason="translated segment is shorter than expected",
            )
        return CompletenessSegment(
            index=index,
            source=source,
            translated=translated,
            source_length=src_len,
            translated_length=dst_len,
            length_ratio=ratio,
            status="ok",
            severity="info",
            reason="segment appears covered",
        )

    def _split_units(self, text: str) -> List[str]:
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text) if p.strip()]
        if len(paragraphs) >= 2:
            return paragraphs
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
        return sentences or [text]
