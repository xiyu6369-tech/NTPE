from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


KOREAN_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")


@dataclass(frozen=True)
class RuntimeQAPolicy:
    enabled: bool = True
    min_length_ratio: float = 0.25
    max_korean_chars: int = 3
    max_repeated_lines: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def count_korean_characters(text: str) -> int:
    return len(KOREAN_RE.findall(text or ""))


def _normalized_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def detect_repeated_lines(text: str, max_repeated_lines: int = 2) -> list[str]:
    counts: dict[str, int] = {}
    repeated: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if len(line) < 4:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] > max_repeated_lines and line not in repeated:
            repeated.append(line)
    return repeated


def analyze_runtime_quality(source_text: str, translated_text: str, policy: RuntimeQAPolicy | None = None) -> dict[str, Any]:
    policy = policy or RuntimeQAPolicy()
    source_len = max(1, _normalized_len(source_text))
    translated_len = _normalized_len(translated_text)
    length_ratio = translated_len / source_len
    korean_chars = count_korean_characters(translated_text)
    repeated_lines = detect_repeated_lines(translated_text, policy.max_repeated_lines)
    issues: list[dict[str, Any]] = []
    if not policy.enabled:
        return {
            "passed": True,
            "enabled": False,
            "issues": [],
            "metrics": {
                "source_chars": source_len,
                "translated_chars": translated_len,
                "length_ratio": round(length_ratio, 4),
                "korean_chars": korean_chars,
                "repeated_line_count": len(repeated_lines),
            },
        }
    if translated_len == 0:
        issues.append({"code": "EMPTY_TRANSLATION", "message": "譯文為空"})
    elif length_ratio < policy.min_length_ratio:
        issues.append({"code": "LENGTH_RATIO_TOO_LOW", "message": f"譯文長度比例過低：{length_ratio:.3f} < {policy.min_length_ratio:.3f}"})
    if korean_chars > policy.max_korean_chars:
        issues.append({"code": "KOREAN_RESIDUE", "message": f"韓文殘留過多：{korean_chars} > {policy.max_korean_chars}"})
    if repeated_lines:
        issues.append({"code": "REPEATED_LINES", "message": f"偵測到重複行：{len(repeated_lines)}", "samples": repeated_lines[:3]})
    return {
        "passed": not issues,
        "enabled": True,
        "issues": issues,
        "metrics": {
            "source_chars": source_len,
            "translated_chars": translated_len,
            "length_ratio": round(length_ratio, 4),
            "korean_chars": korean_chars,
            "repeated_line_count": len(repeated_lines),
        },
    }
