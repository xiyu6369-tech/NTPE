from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TextUnit:
    index: int
    start: int
    end: int
    text: str


def locate_paragraphs(text: str) -> tuple[TextUnit, ...]:
    value = str(text or "")
    units: list[TextUnit] = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)", value, flags=re.DOTALL):
        snippet = match.group(0)
        units.append(TextUnit(len(units), match.start(), match.end(), snippet))
    return tuple(units)


def locate_sentences(text: str) -> tuple[TextUnit, ...]:
    value = str(text or "")
    pattern = re.compile(r"[^。！？!?\n]+[。！？!?]?", re.UNICODE)
    units: list[TextUnit] = []
    for match in pattern.finditer(value):
        snippet = match.group(0).strip()
        if not snippet:
            continue
        start = match.start() + (len(match.group(0)) - len(match.group(0).lstrip()))
        units.append(TextUnit(len(units), start, start + len(snippet), snippet))
    return tuple(units)


def locate_dialogues(text: str) -> tuple[TextUnit, ...]:
    value = str(text or "")
    units: list[TextUnit] = []
    for match in re.finditer(r"[「『](.*?)[」』]", value, flags=re.DOTALL):
        units.append(TextUnit(len(units), match.start(), match.end(), match.group(0)))
    return tuple(units)
