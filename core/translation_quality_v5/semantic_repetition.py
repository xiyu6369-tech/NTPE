from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
_STRIP_RE = re.compile(r"[\s，。！？!?；;：:、\-—…（）()「」『』“”\"']+")


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text or "") if p.strip()]


def _normalize(text: str) -> str:
    return _STRIP_RE.sub("", text or "")


def _ngrams(text: str, size: int = 2) -> set[str]:
    value = _normalize(text)
    if len(value) < size:
        return set()
    return {value[i : i + size] for i in range(len(value) - size + 1)}


def _similarity(left: str, right: str) -> tuple[float, float]:
    a = _normalize(left)
    b = _normalize(right)
    sequence_ratio = SequenceMatcher(None, a, b).ratio()
    a_grams = _ngrams(a)
    b_grams = _ngrams(b)
    union = a_grams | b_grams
    jaccard = len(a_grams & b_grams) / len(union) if union else 0.0
    return sequence_ratio, jaccard


def _find_pairs(
    text: str,
    *,
    min_chars: int = 60,
    window: int = 3,
    strong_sequence: float = 0.78,
    moderate_sequence: float = 0.58,
    moderate_jaccard: float = 0.34,
) -> list[dict[str, Any]]:
    paragraphs = _paragraphs(text)
    hits: list[dict[str, Any]] = []
    for left_index, left in enumerate(paragraphs):
        left_norm = _normalize(left)
        if len(left_norm) < min_chars:
            continue
        upper = min(len(paragraphs), left_index + window + 1)
        for right_index in range(left_index + 1, upper):
            right = paragraphs[right_index]
            right_norm = _normalize(right)
            if len(right_norm) < min_chars:
                continue
            sequence_ratio, jaccard = _similarity(left, right)
            matched = sequence_ratio >= strong_sequence or (
                sequence_ratio >= moderate_sequence and jaccard >= moderate_jaccard
            )
            if not matched:
                continue
            hits.append({
                "left_paragraph": left_index + 1,
                "right_paragraph": right_index + 1,
                "sequence_similarity": round(sequence_ratio, 4),
                "bigram_jaccard": round(jaccard, 4),
                "left_preview": left[:160],
                "right_preview": right[:160],
            })
    return hits


def analyze_semantic_repetition(source_text: str, translated_text: str) -> dict[str, Any]:
    """Detect conservative near-duplicate paragraphs without rewriting text.

    A translated hit is considered suspicious only when the source does not
    contain an equal number of comparable near-duplicate paragraph pairs.
    """
    translated_pairs = _find_pairs(translated_text)
    source_pairs = _find_pairs(source_text)
    suspicious_count = max(0, len(translated_pairs) - len(source_pairs))
    issues: list[dict[str, Any]] = []
    if suspicious_count:
        issues.append({
            "code": "semantic_duplicate_paragraph",
            "severity": "high",
            "message": "譯文出現近似重複段落，疑似重述或重複生成。",
            "repair_action": "retranslate_original_chunk",
            "details": {
                "translated_pair_count": len(translated_pairs),
                "source_pair_count": len(source_pairs),
                "suspicious_pair_count": suspicious_count,
                "pairs": translated_pairs[:6],
            },
        })
    return {
        "issues": issues,
        "metrics": {
            "semantic_duplicate_pair_count": len(translated_pairs),
            "source_semantic_duplicate_pair_count": len(source_pairs),
            "suspicious_semantic_duplicate_pair_count": suspicious_count,
        },
    }
