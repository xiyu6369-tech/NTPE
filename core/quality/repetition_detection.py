# =====================================================
# NTPE 1.2 Professional
# Stage-15.4 Repetition / Duplicate Content Detection
# =====================================================

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class RepetitionSpan:
    """A repeated or near-duplicate text span detected in translated output."""

    span_type: str
    text: str
    count: int
    first_index: int
    indexes: Tuple[int, ...]
    severity: str = "warning"
    similarity: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        return hashlib.sha1(self.text.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_type": self.span_type,
            "text": self.text,
            "count": self.count,
            "first_index": self.first_index,
            "indexes": list(self.indexes),
            "severity": self.severity,
            "similarity": round(float(self.similarity), 4),
            "fingerprint": self.fingerprint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RepetitionAnalysis:
    spans: List[RepetitionSpan]
    metrics: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not any(span.severity in {"error", "critical"} for span in self.spans)

    @property
    def warning_count(self) -> int:
        return sum(1 for span in self.spans if span.severity == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for span in self.spans if span.severity in {"error", "critical"})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "spans": [span.to_dict() for span in self.spans],
            "metrics": dict(self.metrics),
        }


class RepetitionDetector:
    """Deterministic duplicate-content detector for translated novel text.

    The detector is provider-independent. It checks exact duplicate paragraphs,
    exact duplicate sentences, repeated n-grams, and adjacent near-duplicates.
    This catches common LLM failure modes such as repeated paragraphs, looped
    sentences, and duplicated output blocks without mutating translated text.
    """

    def __init__(
        self,
        *,
        paragraph_min_chars: int = 12,
        sentence_min_chars: int = 8,
        duplicate_threshold: int = 2,
        critical_threshold: int = 3,
        near_duplicate_similarity: float = 0.94,
        ngram_size: int = 18,
        ngram_repeat_threshold: int = 4,
    ) -> None:
        self.paragraph_min_chars = max(1, int(paragraph_min_chars))
        self.sentence_min_chars = max(1, int(sentence_min_chars))
        self.duplicate_threshold = max(2, int(duplicate_threshold))
        self.critical_threshold = max(self.duplicate_threshold, int(critical_threshold))
        self.near_duplicate_similarity = min(1.0, max(0.0, float(near_duplicate_similarity)))
        self.ngram_size = max(4, int(ngram_size))
        self.ngram_repeat_threshold = max(2, int(ngram_repeat_threshold))

    def analyze(self, translated_text: str) -> RepetitionAnalysis:
        text = translated_text or ""
        paragraphs = self._split_paragraphs(text)
        sentences = self._split_sentences(text)
        spans: List[RepetitionSpan] = []
        spans.extend(self._exact_duplicates(paragraphs, "paragraph", self.paragraph_min_chars))
        spans.extend(self._exact_duplicates(sentences, "sentence", self.sentence_min_chars))
        spans.extend(self._adjacent_near_duplicates(paragraphs))
        spans.extend(self._repeated_ngrams(text))
        spans = self._deduplicate_spans(spans)
        repeated_chars = sum(len(span.text) * max(0, span.count - 1) for span in spans)
        metrics = {
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "span_count": len(spans),
            "repeated_character_estimate": repeated_chars,
            "repetition_ratio": round(repeated_chars / max(1, len(text)), 4),
            "duplicate_threshold": self.duplicate_threshold,
            "critical_threshold": self.critical_threshold,
            "near_duplicate_similarity": self.near_duplicate_similarity,
        }
        return RepetitionAnalysis(spans=spans, metrics=metrics)

    def _split_paragraphs(self, text: str) -> List[str]:
        return [p.strip() for p in re.split(r"\n\s*\n|\r?\n", text or "") if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r"(?<=[。！？!?])\s*|\n+", text or "")
        return [p.strip() for p in parts if p and p.strip()]

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", "", value or "").strip()

    def _exact_duplicates(self, items: Sequence[str], span_type: str, min_chars: int) -> List[RepetitionSpan]:
        buckets: Dict[str, List[int]] = {}
        originals: Dict[str, str] = {}
        for idx, item in enumerate(items):
            normalized = self._normalize(item)
            if len(normalized) < min_chars:
                continue
            buckets.setdefault(normalized, []).append(idx)
            originals.setdefault(normalized, item.strip())
        spans: List[RepetitionSpan] = []
        for normalized, indexes in buckets.items():
            if len(indexes) >= self.duplicate_threshold:
                severity = "critical" if len(indexes) >= self.critical_threshold else "warning"
                spans.append(
                    RepetitionSpan(
                        span_type=f"duplicate_{span_type}",
                        text=originals[normalized],
                        count=len(indexes),
                        first_index=indexes[0],
                        indexes=tuple(indexes),
                        severity=severity,
                        metadata={"normalized_length": len(normalized)},
                    )
                )
        return spans

    def _adjacent_near_duplicates(self, paragraphs: Sequence[str]) -> List[RepetitionSpan]:
        spans: List[RepetitionSpan] = []
        for idx in range(len(paragraphs) - 1):
            left = self._normalize(paragraphs[idx])
            right = self._normalize(paragraphs[idx + 1])
            if min(len(left), len(right)) < self.paragraph_min_chars:
                continue
            if left == right:
                continue
            similarity = SequenceMatcher(None, left, right).ratio()
            if similarity >= self.near_duplicate_similarity:
                spans.append(
                    RepetitionSpan(
                        span_type="near_duplicate_adjacent_paragraph",
                        text=paragraphs[idx].strip(),
                        count=2,
                        first_index=idx,
                        indexes=(idx, idx + 1),
                        severity="warning",
                        similarity=similarity,
                        metadata={"next_text": paragraphs[idx + 1].strip()},
                    )
                )
        return spans

    def _repeated_ngrams(self, text: str) -> List[RepetitionSpan]:
        normalized = self._normalize(text)
        if len(normalized) < self.ngram_size * self.ngram_repeat_threshold:
            return []
        buckets: Dict[str, List[int]] = {}
        for i in range(0, len(normalized) - self.ngram_size + 1, max(1, self.ngram_size // 3)):
            gram = normalized[i : i + self.ngram_size]
            buckets.setdefault(gram, []).append(i)
        spans: List[RepetitionSpan] = []
        for gram, positions in buckets.items():
            if len(positions) >= self.ngram_repeat_threshold:
                spans.append(
                    RepetitionSpan(
                        span_type="repeated_ngram",
                        text=gram,
                        count=len(positions),
                        first_index=positions[0],
                        indexes=tuple(positions),
                        severity="warning" if len(positions) < self.critical_threshold * 2 else "critical",
                        metadata={"ngram_size": self.ngram_size},
                    )
                )
        return spans[:25]

    def _deduplicate_spans(self, spans: Iterable[RepetitionSpan]) -> List[RepetitionSpan]:
        seen = set()
        result: List[RepetitionSpan] = []
        for span in spans:
            key = (span.span_type, self._normalize(span.text), span.indexes)
            if key in seen:
                continue
            seen.add(key)
            result.append(span)
        result.sort(key=lambda s: (0 if s.severity == "critical" else 1, s.first_index, s.span_type))
        return result
