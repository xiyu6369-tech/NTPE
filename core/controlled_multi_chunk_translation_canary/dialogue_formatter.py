"""Deterministic Stage 7.4 dialogue-quote normalization."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_DIALOGUE_TERMINATORS = frozenset("。！？!?…，、；：")
_AMBIGUOUS_CONTENT_MARKS = frozenset("\"“”‘’「」『』`\\{}[]")


@dataclass(frozen=True)
class Stage74DialogueFormattingResult:
    raw_candidate_fingerprint: str
    normalized_candidate_fingerprint: str
    normalized_text: str
    converted_pair_count: int
    changed: bool
    eligible: bool
    reason_codes: tuple[str, ...]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _paired_spans(
    text: str,
    opening: str,
    closing: str,
    *,
    label: str,
) -> tuple[tuple[tuple[int, int, str], ...], tuple[str, ...]]:
    spans: list[tuple[int, int, str]] = []
    reasons: list[str] = []
    active: int | None = None
    for position, mark in enumerate(text):
        if mark == opening:
            if active is not None:
                reasons.append(f"ambiguous-nested-{label}-quote")
            else:
                active = position
        elif mark == closing:
            if active is None:
                reasons.append(f"unmatched-{label}-closing-quote")
            else:
                spans.append((active, position, text[active + 1:position]))
                active = None
    if active is not None:
        reasons.append(f"unmatched-{label}-opening-quote")
    return tuple(spans), tuple(dict.fromkeys(reasons))


def _source_dialogue_pair_count(source: str) -> int:
    for opening, closing, label in (
        ("“", "”", "source-curly"),
        ("「", "」", "source-corner"),
        ('"', '"', "source-ascii"),
    ):
        if opening not in source and closing not in source:
            continue
        if opening == closing:
            count = source.count(opening)
            return count // 2 if count and count % 2 == 0 else 0
        spans, reasons = _paired_spans(
            source, opening, closing, label=label
        )
        return len(spans) if not reasons else 0
    return 0


def normalize_stage74_dialogue_quotes(
    source: str,
    candidate: str,
) -> Stage74DialogueFormattingResult:
    """Convert only unambiguous balanced Chinese dialogue ``“…”`` to ``「…」``.

    Unsafe or ambiguous input is returned byte-identically so the existing
    mandatory dialogue gate can reject it.
    """
    source = source or ""
    candidate = candidate or ""
    raw_fingerprint = _sha256_text(candidate)

    curly_present = "“" in candidate or "”" in candidate
    if not curly_present:
        return Stage74DialogueFormattingResult(
            raw_candidate_fingerprint=raw_fingerprint,
            normalized_candidate_fingerprint=raw_fingerprint,
            normalized_text=candidate,
            converted_pair_count=0,
            changed=False,
            eligible=True,
            reason_codes=(),
        )

    reasons: list[str] = []
    if any(mark in candidate for mark in ("「", "」", '"')):
        reasons.append("mixed-dialogue-quote-systems")
    if any(mark in candidate for mark in ("‘", "’")):
        reasons.append("ambiguous-curly-nesting")
    stripped = candidate.lstrip()
    if stripped.startswith(("{", "[", "```")):
        reasons.append("code-like-candidate")

    spans, pairing_reasons = _paired_spans(
        candidate, "“", "”", label="curly"
    )
    reasons.extend(pairing_reasons)
    source_pair_count = _source_dialogue_pair_count(source)
    if source_pair_count == 0:
        reasons.append("source-dialogue-not-proven")
    elif len(spans) != source_pair_count:
        reasons.append("source-candidate-dialogue-count-mismatch")

    for _, _, content in spans:
        stripped_content = content.rstrip()
        if not stripped_content:
            reasons.append("empty-curly-dialogue")
            continue
        if "\n" in content or "\r" in content:
            reasons.append("multiline-curly-dialogue-ambiguous")
        if not _CJK_RE.search(content):
            reasons.append("non-chinese-curly-content")
        if stripped_content[-1] not in _DIALOGUE_TERMINATORS:
            reasons.append("curly-dialogue-closing-punctuation-missing")
        if any(mark in content for mark in _AMBIGUOUS_CONTENT_MARKS):
            reasons.append("ambiguous-nested-or-code-like-curly-content")

    reason_codes = tuple(dict.fromkeys(reasons))
    if reason_codes:
        return Stage74DialogueFormattingResult(
            raw_candidate_fingerprint=raw_fingerprint,
            normalized_candidate_fingerprint=raw_fingerprint,
            normalized_text=candidate,
            converted_pair_count=0,
            changed=False,
            eligible=False,
            reason_codes=reason_codes,
        )

    characters = list(candidate)
    for opening, closing, _ in spans:
        characters[opening] = "「"
        characters[closing] = "」"
    normalized = "".join(characters)
    return Stage74DialogueFormattingResult(
        raw_candidate_fingerprint=raw_fingerprint,
        normalized_candidate_fingerprint=_sha256_text(normalized),
        normalized_text=normalized,
        converted_pair_count=len(spans),
        changed=normalized != candidate,
        eligible=True,
        reason_codes=(),
    )
