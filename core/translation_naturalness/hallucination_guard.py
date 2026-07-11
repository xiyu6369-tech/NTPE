from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

UNSUPPORTED_DETAIL_GUARD_VERSION = "6.0.0-stage12.2"

_TRANSPORT_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("小型飛機", ("소형 비행기", "경비행기", "소형기")),
    ("私人飛機", ("전용기", "개인 비행기")),
    ("直升機", ("헬리콥터", "회전익기")),
    ("快艇", ("쾌속정", "고속정")),
    ("遊艇", ("요트",)),
)

_GENERIC_ISLAND_FORMS = {
    "這個島", "這座島", "那個島", "那座島", "本島", "該島", "小島", "島嶼", "南國島嶼", "南方島嶼",
}

_NUMBER_ALIASES: dict[int, tuple[str, ...]] = {
    1: ("1", "一", "하루", "한", "일"),
    2: ("2", "二", "兩", "이틀", "두", "이"),
    3: ("3", "三", "사흘", "세", "삼"),
    4: ("4", "四", "나흘", "네", "사"),
    5: ("5", "五", "닷새", "다섯", "오"),
    6: ("6", "六", "엿새", "여섯", "육"),
    7: ("7", "七", "이레", "일곱", "칠"),
    8: ("8", "八", "여드레", "여덟", "팔"),
    9: ("9", "九", "아흐레", "아홉", "구"),
    10: ("10", "十", "열흘", "열", "십"),
}

_CHINESE_NUMBER_TO_INT = {
    "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


@dataclass(frozen=True)
class UnsupportedDetailGuardResult:
    issues: tuple[dict[str, Any], ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def blocking(self) -> bool:
        return any(bool(item.get("retry_required")) for item in self.issues)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": UNSUPPORTED_DETAIL_GUARD_VERSION,
            "issue_count": len(self.issues),
            "warning_count": len(self.warnings),
            "blocking": self.blocking,
            "issues": [dict(item) for item in self.issues],
            "warnings": [dict(item) for item in self.warnings],
            "provider_called": False,
            "semantic_rewrite_allowed": False,
            "fail_closed": True,
            **dict(self.metadata),
        }


def _issue(code: str, message: str, evidence: dict[str, Any], *, confidence: float) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "high",
        "message": message,
        "evidence": evidence,
        "retry_required": True,
        "repair_action": "provider_regeneration_required",
        "metadata": {
            "detector": "unsupported_detail_guard",
            "confidence": confidence,
            "reliable": True,
            "guard_version": UNSUPPORTED_DETAIL_GUARD_VERSION,
        },
    }


def _source_has_duration(source: str, number: int, unit: str) -> bool:
    aliases = _NUMBER_ALIASES.get(number, (str(number),))
    if unit == "day":
        unit_terms = ("일", "날", "동안")
    else:
        unit_terms = ("시간", "시")
    for alias in aliases:
        if any(f"{alias}{term}" in source or f"{alias} {term}" in source for term in unit_terms):
            return True
        if alias in {"하루", "이틀", "사흘", "나흘", "닷새", "엿새", "이레", "여드레", "아흐레", "열흘"} and alias in source:
            return True
    return False


def analyze_unsupported_details(source_text: str, translated_text: str) -> UnsupportedDetailGuardResult:
    source = str(source_text or "")
    translated = str(translated_text or "")
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    # Transportation specificity: only block when a controlled Chinese term is
    # present and none of its Korean source aliases appears.
    for translated_term, source_aliases in _TRANSPORT_TERMS:
        if translated_term in translated and not any(alias in source for alias in source_aliases):
            issues.append(_issue(
                "ADDED_DETAIL",
                f"譯文新增原文未支持的具體交通工具：{translated_term}",
                {"translated_term": translated_term, "expected_source_aliases": list(source_aliases)},
                confidence=0.98,
            ))

    # Proper-name-like island additions. Generic island wording is explicitly
    # exempt. A named island is only blocked when the source has no Korean
    # proper-name + 섬 construction and only contains a generic island mention.
    raw_islands = {match.group(1) for match in re.finditer(r"(?=([\u4e00-\u9fff]{2,6}島))", translated)}
    generic_markers = set("這那本該小南座個往到於在的")
    named_islands = {
        item for item in raw_islands
        if item not in _GENERIC_ISLAND_FORMS
        and not any(marker in item for marker in generic_markers)
    }
    source_named_island = bool(re.search(r"[가-힣]{2,12}\s*섬", source))
    if named_islands and not source_named_island:
        for island in sorted(named_islands):
            issues.append(_issue(
                "HALLUCINATION",
                f"譯文出現原文未支持的專名式島名：{island}",
                {"translated_term": island, "source_named_island_detected": False},
                confidence=0.93,
            ))

    # Explicit day/hour counts. Only numbers 1-10 are covered because those can
    # be corroborated against a conservative Korean alias table.
    for raw_number, unit_text in re.findall(r"([一二兩三四五六七八九十]|\d{1,2})\s*(天|日|小時)", translated):
        number = int(raw_number) if raw_number.isdigit() else _CHINESE_NUMBER_TO_INT.get(raw_number)
        if not number or number > 10:
            warnings.append({
                "code": "UNSUPPORTED_TIME_DETAIL_UNVERIFIED",
                "translated_evidence": f"{raw_number}{unit_text}",
                "auto_blocked": False,
            })
            continue
        unit = "hour" if unit_text == "小時" else "day"
        if not _source_has_duration(source, number, unit):
            issues.append(_issue(
                "ADDED_DETAIL",
                f"譯文新增原文未支持的具體時間：{raw_number}{unit_text}",
                {"translated_evidence": f"{raw_number}{unit_text}", "number": number, "unit": unit},
                confidence=0.91,
            ))

    # Deduplicate identical code/evidence pairs while preserving order.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in issues:
        key = (str(item.get("code")), repr(item.get("evidence")))
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return UnsupportedDetailGuardResult(
        issues=tuple(deduped),
        warnings=tuple(warnings),
        metadata={
            "detectors": ["transport_specificity", "named_island", "explicit_duration"],
            "source_length": len(source),
            "translated_length": len(translated),
        },
    )
