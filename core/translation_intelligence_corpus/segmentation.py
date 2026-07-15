from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class _Span:
    start: int
    end: int


_OPEN_TO_CLOSE = {"\u201c": "\u201d", "\u2018": "\u2019", "\u300c": "\u300d", "\u300e": "\u300f", "(": ")", "[": "]", "{": "}"}
_CLOSERS = set(_OPEN_TO_CLOSE.values())


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _paragraph_spans(text: str) -> list[_Span]:
    if not text:
        return []
    spans: list[_Span] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] == "\n":
            end = index + 1
            while end < len(text) and text[end] in " \t\r\n":
                end += 1
            if text[index:end].count("\n") >= 2:
                spans.append(_Span(start, end))
                start = end
                index = end
                continue
        index += 1
    if start < len(text):
        spans.append(_Span(start, len(text)))
    return [span for span in spans if span.end > span.start]


def _sentence_spans(text: str, paragraph: _Span, language: str) -> list[_Span]:
    terminal = {".", "!", "?"} if language == "ko" else {"\u3002", "\uff01", "\uff1f", "!", "?"}
    stack: list[str] = []
    spans: list[_Span] = []
    start = paragraph.start
    pending_terminal = False
    index = paragraph.start
    while index < paragraph.end:
        char = text[index]
        if char in _OPEN_TO_CLOSE:
            stack.append(_OPEN_TO_CLOSE[char])
        elif char in _CLOSERS and stack and stack[-1] == char:
            stack.pop()
        if char in terminal:
            pending_terminal = True
        if pending_terminal and not stack:
            end = index + 1
            while end < paragraph.end and text[end].isspace():
                end += 1
            if end > start:
                spans.append(_Span(start, end))
            start = end
            index = end
            pending_terminal = False
            continue
        index += 1
    if start < paragraph.end:
        spans.append(_Span(start, paragraph.end))
    return spans or [paragraph]


def _segment_type(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "unknown"
    quote_chars = "\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f"
    contains_quote = any(char in stripped for char in quote_chars)
    starts_quote = stripped[0] in "\u201c\u2018\u300c\u300e"
    if starts_quote and stripped[-1] in "\u201d\u2019\u300d\u300f":
        return "dialogue"
    if contains_quote:
        return "mixed"
    return "narrative"


def segment_text(text: str, *, case_id: str, language: str) -> list[dict[str, object]]:
    """Split Korean or Traditional Chinese without rewriting any codepoint."""
    if language not in {"ko", "zh-Hant"}:
        raise ValueError("language must be 'ko' or 'zh-Hant'")
    segments: list[dict[str, object]] = []
    for paragraph_index, paragraph in enumerate(_paragraph_spans(text)):
        for span in _sentence_spans(text, paragraph, "ko" if language == "ko" else "zh"):
            value = text[span.start : span.end]
            index = len(segments)
            identity = f"{case_id}|{language}|{index}|{span.start}|{span.end}|{_sha256_text(value)}"
            segments.append(
                {
                    "segment_id": "TIC-SEG-B3-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper(),
                    "case_id": case_id,
                    "language": language,
                    "segment_type": _segment_type(value),
                    "segment_index": index,
                    "paragraph_index": paragraph_index,
                    "start_offset": span.start,
                    "end_offset": span.end,
                    "text": value,
                    "text_sha256": _sha256_text(value),
                }
            )
    return segments


def reconstruct_text(segments: list[dict[str, object]]) -> str:
    return "".join(str(segment["text"]) for segment in segments)
