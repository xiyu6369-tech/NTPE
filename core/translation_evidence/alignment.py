from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence

from .locator import TextUnit, locate_paragraphs, locate_sentences

ALIGNMENT_SCHEMA_VERSION = "6.0.0-stage11.2"
ALIGNMENT_ENGINE_VERSION = "6.0.0-stage11.2"


@dataclass(frozen=True)
class AlignmentSpan:
    alignment_type: str
    source_indexes: tuple[int, ...]
    translated_indexes: tuple[int, ...]
    source_start: int
    source_end: int
    translated_start: int
    translated_end: int
    confidence: float
    reliable: bool
    operation: str = "1:1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.alignment_type or "").strip().lower()
        if kind not in {"paragraph", "sentence"}:
            raise ValueError(f"unsupported alignment_type: {kind}")
        confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.source_end < self.source_start or self.translated_end < self.translated_start:
            raise ValueError("alignment ranges must be monotonic")
        object.__setattr__(self, "alignment_type", kind)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": ALIGNMENT_SCHEMA_VERSION,
            "alignment_type": self.alignment_type,
            "source_indexes": list(self.source_indexes),
            "translated_indexes": list(self.translated_indexes),
            "source_start": self.source_start,
            "source_end": self.source_end,
            "translated_start": self.translated_start,
            "translated_end": self.translated_end,
            "confidence": self.confidence,
            "reliable": bool(self.reliable),
            "operation": self.operation,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SemanticAlignmentResult:
    paragraph_alignments: tuple[AlignmentSpan, ...]
    sentence_alignments: tuple[AlignmentSpan, ...]
    unaligned_source_paragraphs: tuple[int, ...]
    unaligned_translated_paragraphs: tuple[int, ...]
    confidence: float
    reliable: bool
    statistics: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": ALIGNMENT_SCHEMA_VERSION,
            "engine_version": ALIGNMENT_ENGINE_VERSION,
            "paragraph_alignments": [item.to_dict() for item in self.paragraph_alignments],
            "sentence_alignments": [item.to_dict() for item in self.sentence_alignments],
            "unaligned_source_paragraphs": list(self.unaligned_source_paragraphs),
            "unaligned_translated_paragraphs": list(self.unaligned_translated_paragraphs),
            "confidence": self.confidence,
            "reliable": bool(self.reliable),
            "statistics": dict(self.statistics),
            "metadata": dict(self.metadata),
        }


def _dialogue_flag(text: str) -> bool:
    value = str(text or "")
    return any(mark in value for mark in ('"', "“", "”", "‘", "’", "「", "」", "『", "』"))


def _length_score(source_text: str, translated_text: str) -> float:
    source_len = max(1, len("".join(str(source_text or "").split())))
    translated_len = max(1, len("".join(str(translated_text or "").split())))
    ratio = min(source_len, translated_len) / max(source_len, translated_len)
    # Cross-language character counts differ materially. Keep the score conservative,
    # but do not punish normal Korean->Chinese compression too aggressively.
    return min(1.0, ratio / 0.58) if ratio < 0.58 else 1.0 - min(0.35, (ratio - 0.58) * 0.30)


def _position_score(source_indexes: Sequence[int], translated_indexes: Sequence[int], source_count: int, translated_count: int) -> float:
    if not source_indexes or not translated_indexes:
        return 0.0
    source_center = (source_indexes[0] + source_indexes[-1] + 1.0) / (2.0 * max(1, source_count))
    translated_center = (translated_indexes[0] + translated_indexes[-1] + 1.0) / (2.0 * max(1, translated_count))
    return max(0.0, 1.0 - abs(source_center - translated_center) * 1.8)


def _group_text(units: Sequence[TextUnit], indexes: Sequence[int]) -> str:
    return "\n".join(units[index].text for index in indexes)


def _pair_score(
    source_units: Sequence[TextUnit],
    translated_units: Sequence[TextUnit],
    source_indexes: Sequence[int],
    translated_indexes: Sequence[int],
) -> float:
    source_text = _group_text(source_units, source_indexes)
    translated_text = _group_text(translated_units, translated_indexes)
    length = _length_score(source_text, translated_text)
    position = _position_score(source_indexes, translated_indexes, len(source_units), len(translated_units))
    dialogue = 1.0 if _dialogue_flag(source_text) == _dialogue_flag(translated_text) else 0.35
    merge_penalty = 0.05 * (max(0, len(source_indexes) - 1) + max(0, len(translated_indexes) - 1))
    return max(0.0, min(1.0, 0.43 * position + 0.37 * length + 0.20 * dialogue - merge_penalty))


def _align_units(source_units: Sequence[TextUnit], translated_units: Sequence[TextUnit], *, alignment_type: str) -> tuple[tuple[AlignmentSpan, ...], tuple[int, ...], tuple[int, ...]]:
    n, m = len(source_units), len(translated_units)
    if not n or not m:
        return (), tuple(range(n)), tuple(range(m))

    # Monotonic dynamic programming with conservative 1:1, 2:1 and 1:2 links.
    neg = -10**9
    dp = [[neg] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[int, int, tuple[int, ...], tuple[int, ...], float] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    operations = ((1, 1), (2, 1), (1, 2))
    gap_penalty = 0.72

    for i in range(n + 1):
        for j in range(m + 1):
            if dp[i][j] <= neg / 2:
                continue
            if i < n and dp[i][j] - gap_penalty > dp[i + 1][j]:
                dp[i + 1][j] = dp[i][j] - gap_penalty
                back[i + 1][j] = (i, j, (i,), (), 0.0)
            if j < m and dp[i][j] - gap_penalty > dp[i][j + 1]:
                dp[i][j + 1] = dp[i][j] - gap_penalty
                back[i][j + 1] = (i, j, (), (j,), 0.0)
            for source_size, translated_size in operations:
                if i + source_size > n or j + translated_size > m:
                    continue
                source_indexes = tuple(range(i, i + source_size))
                translated_indexes = tuple(range(j, j + translated_size))
                score = _pair_score(source_units, translated_units, source_indexes, translated_indexes)
                candidate = dp[i][j] + score
                if candidate > dp[i + source_size][j + translated_size]:
                    dp[i + source_size][j + translated_size] = candidate
                    back[i + source_size][j + translated_size] = (i, j, source_indexes, translated_indexes, score)

    aligned: list[AlignmentSpan] = []
    unaligned_source: list[int] = []
    unaligned_translated: list[int] = []
    i, j = n, m
    while i or j:
        step = back[i][j]
        if step is None:
            # Defensive fallback; never invent a range.
            if i:
                i -= 1
                unaligned_source.append(i)
            elif j:
                j -= 1
                unaligned_translated.append(j)
            continue
        prev_i, prev_j, source_indexes, translated_indexes, score = step
        if source_indexes and translated_indexes:
            source_start = source_units[source_indexes[0]].start
            source_end = source_units[source_indexes[-1]].end
            translated_start = translated_units[translated_indexes[0]].start
            translated_end = translated_units[translated_indexes[-1]].end
            threshold = 0.76 if len(source_indexes) == len(translated_indexes) == 1 else 0.82
            aligned.append(
                AlignmentSpan(
                    alignment_type=alignment_type,
                    source_indexes=source_indexes,
                    translated_indexes=translated_indexes,
                    source_start=source_start,
                    source_end=source_end,
                    translated_start=translated_start,
                    translated_end=translated_end,
                    confidence=score,
                    reliable=score >= threshold,
                    operation=f"{len(source_indexes)}:{len(translated_indexes)}",
                    metadata={
                        "length_score": _length_score(_group_text(source_units, source_indexes), _group_text(translated_units, translated_indexes)),
                        "dialogue_consistent": _dialogue_flag(_group_text(source_units, source_indexes)) == _dialogue_flag(_group_text(translated_units, translated_indexes)),
                    },
                )
            )
        elif source_indexes:
            unaligned_source.extend(source_indexes)
        elif translated_indexes:
            unaligned_translated.extend(translated_indexes)
        i, j = prev_i, prev_j

    aligned.reverse()
    return tuple(aligned), tuple(sorted(unaligned_source)), tuple(sorted(unaligned_translated))


def _sentence_alignments(
    source_text: str,
    translated_text: str,
    paragraph_alignments: Iterable[AlignmentSpan],
) -> tuple[AlignmentSpan, ...]:
    source_paragraphs = locate_paragraphs(source_text)
    translated_paragraphs = locate_paragraphs(translated_text)
    results: list[AlignmentSpan] = []
    for paragraph_alignment in paragraph_alignments:
        source_segment = source_text[paragraph_alignment.source_start:paragraph_alignment.source_end]
        translated_segment = translated_text[paragraph_alignment.translated_start:paragraph_alignment.translated_end]
        source_sentences = locate_sentences(source_segment)
        translated_sentences = locate_sentences(translated_segment)
        local, _missing_source, _missing_translated = _align_units(source_sentences, translated_sentences, alignment_type="sentence")
        for item in local:
            results.append(
                AlignmentSpan(
                    alignment_type="sentence",
                    source_indexes=item.source_indexes,
                    translated_indexes=item.translated_indexes,
                    source_start=item.source_start + paragraph_alignment.source_start,
                    source_end=item.source_end + paragraph_alignment.source_start,
                    translated_start=item.translated_start + paragraph_alignment.translated_start,
                    translated_end=item.translated_end + paragraph_alignment.translated_start,
                    confidence=min(item.confidence, paragraph_alignment.confidence),
                    reliable=bool(item.reliable and paragraph_alignment.reliable),
                    operation=item.operation,
                    metadata={
                        **dict(item.metadata),
                        "parent_source_paragraph_indexes": list(paragraph_alignment.source_indexes),
                        "parent_translated_paragraph_indexes": list(paragraph_alignment.translated_indexes),
                    },
                )
            )
    return tuple(results)


def build_source_translation_alignment(source_text: str, translated_text: str) -> SemanticAlignmentResult:
    source = str(source_text or "")
    translated = str(translated_text or "")
    source_paragraphs = locate_paragraphs(source)
    translated_paragraphs = locate_paragraphs(translated)
    paragraph_alignments, missing_source, missing_translated = _align_units(
        source_paragraphs,
        translated_paragraphs,
        alignment_type="paragraph",
    )
    sentence_alignments = _sentence_alignments(source, translated, paragraph_alignments)
    confidence_values = [item.confidence for item in paragraph_alignments]
    confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    reliable_count = sum(1 for item in paragraph_alignments if item.reliable)
    reliable = bool(paragraph_alignments) and not missing_source and reliable_count == len(paragraph_alignments)
    if not isfinite(confidence):
        confidence = 0.0
    return SemanticAlignmentResult(
        paragraph_alignments=paragraph_alignments,
        sentence_alignments=sentence_alignments,
        unaligned_source_paragraphs=missing_source,
        unaligned_translated_paragraphs=missing_translated,
        confidence=max(0.0, min(1.0, confidence)),
        reliable=reliable,
        statistics={
            "source_paragraph_count": len(source_paragraphs),
            "translated_paragraph_count": len(translated_paragraphs),
            "paragraph_alignment_count": len(paragraph_alignments),
            "reliable_paragraph_alignment_count": reliable_count,
            "sentence_alignment_count": len(sentence_alignments),
            "unaligned_source_paragraph_count": len(missing_source),
            "unaligned_translated_paragraph_count": len(missing_translated),
        },
        metadata={
            "engine_version": ALIGNMENT_ENGINE_VERSION,
            "runtime_integrated": False,
            "alignment_policy": "monotonic_fail_closed",
            "allowed_operations": ["1:1", "2:1", "1:2"],
        },
    )
