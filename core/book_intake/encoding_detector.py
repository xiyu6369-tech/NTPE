from __future__ import annotations

import unicodedata
from typing import Final

from .errors import AmbiguousEncodingError, EncodingNotDetectedError
from .models import EncodingDetectionResult

_CANONICAL_ENCODINGS: Final[tuple[str, ...]] = (
    "utf-8",
    "utf-16-le",
    "utf-16-be",
    "cp949",
    "euc-kr",
    "shift-jis",
)

_BOM_SIGNATURES: Final[dict[bytes, tuple[str, str]]] = {
    b"\xef\xbb\xbf": ("utf-8", "bom"),
    b"\xff\xfe": ("utf-16-le", "bom"),
    b"\xfe\xff": ("utf-16-be", "bom"),
}


class EncodingDetector:
    def __init__(self) -> None:
        self._priority = list(_CANONICAL_ENCODINGS)

    def _detect_utf16_heuristic(self, raw_bytes: bytes) -> str | None:
        if len(raw_bytes) < 4 or len(raw_bytes) % 2 != 0:
            return None
        if raw_bytes.count(0) == len(raw_bytes):
            return None

        even_nulls = sum(1 for i in range(0, len(raw_bytes), 2) if raw_bytes[i] == 0)
        odd_nulls = sum(1 for i in range(1, len(raw_bytes), 2) if raw_bytes[i] == 0)
        if even_nulls > odd_nulls and even_nulls >= 2:
            return "utf-16-be"
        if odd_nulls > even_nulls and odd_nulls >= 2:
            return "utf-16-le"
        return None

    def _analyze_text_features(self, text: str) -> dict[str, int]:
        hangul = 0
        hiragana = 0
        katakana = 0
        cjk_ideographs = 0
        control_chars = 0
        replacement_chars = 0

        for char in text:
            if "\uAC00" <= char <= "\uD7A3":
                hangul += 1
            elif "\u3040" <= char <= "\u309F":
                hiragana += 1
            elif "\u30A0" <= char <= "\u30FF":
                katakana += 1
            elif "\u4E00" <= char <= "\u9FFF":
                cjk_ideographs += 1
            elif char == "\uFFFD":
                replacement_chars += 1
            elif unicodedata.category(char).startswith("C") and char not in "\t\n\r\f\v":
                control_chars += 1

        return {
            "hangul": hangul,
            "hiragana": hiragana,
            "katakana": katakana,
            "cjk_ideographs": cjk_ideographs,
            "control_chars": control_chars,
            "replacement_chars": replacement_chars,
        }

    def _score_features(self, features: dict[str, int]) -> int:
        score = 0
        score += features["hangul"] * 4
        score += features["hiragana"] * 3
        score += features["katakana"] * 3
        score += min(features["cjk_ideographs"], 2)
        score -= features["control_chars"] * 3
        score -= features["replacement_chars"] * 5
        return score

    def _try_decode(self, raw_bytes: bytes, encoding: str) -> tuple[str, dict[str, int]] | None:
        try:
            text = raw_bytes.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            return None

        if "\uFFFD" in text:
            return None

        return text, self._analyze_text_features(text)

    def detect(self, raw_bytes: bytes) -> EncodingDetectionResult:
        if not raw_bytes:
            raise EncodingNotDetectedError("No bytes to inspect")

        for bom, (encoding, method) in _BOM_SIGNATURES.items():
            if raw_bytes.startswith(bom):
                return EncodingDetectionResult(
                    encoding=encoding,
                    confidence="high",
                    detection_method=method,
                    bom_present=True,
                    candidates=(encoding,),
                    evidence=(f"BOM detected: {encoding}",),
                )

        utf16_hint = self._detect_utf16_heuristic(raw_bytes)
        if utf16_hint is not None:
            return EncodingDetectionResult(
                encoding=utf16_hint,
                confidence="medium",
                detection_method="heuristic",
                bom_present=False,
                candidates=(utf16_hint,),
                evidence=(f"UTF-16 heuristic detected via null-byte distribution: {utf16_hint}",),
            )

        if b"\x00" in raw_bytes:
            raise EncodingNotDetectedError("No supported encoding could be determined")

        utf8_result = self._try_decode(raw_bytes, "utf-8")
        if utf8_result is not None:
            return EncodingDetectionResult(
                encoding="utf-8",
                confidence="high",
                detection_method="strict",
                bom_present=False,
                candidates=("utf-8",),
                evidence=("UTF-8 strict decode succeeded",),
            )

        candidate_results: list[tuple[str, str, dict[str, int], int]] = []
        for encoding in ("cp949", "euc-kr", "shift-jis"):
            decoded = self._try_decode(raw_bytes, encoding)
            if decoded is None:
                continue
            text, features = decoded
            candidate_results.append((encoding, text, features, self._score_features(features)))

        if candidate_results:
            candidate_results.sort(key=lambda item: item[3], reverse=True)
            best_score = candidate_results[0][3]
            top_candidates = [item for item in candidate_results if item[3] == best_score]

            japanese_candidates = [item for item in candidate_results if item[2]["hiragana"] > 0 or item[2]["katakana"] > 0]
            if japanese_candidates and best_score > 0:
                return EncodingDetectionResult(
                    encoding="shift-jis",
                    confidence="medium",
                    detection_method="heuristic",
                    bom_present=False,
                    candidates=("shift-jis",),
                    evidence=("Japanese kana features were detected; Shift-JIS selected",),
                )

            korean_candidates = [item for item in candidate_results if item[2]["hangul"] > 0 and item[0] in {"cp949", "euc-kr"}]
            if korean_candidates:
                selected_encoding = "cp949" if "cp949" in {item[0] for item in korean_candidates} else "euc-kr"
                evidence = (
                    "Korean language features were detected; CP949/EUC-KR overlap preserved",
                    "Ambiguity preserved in candidates",
                )
                return EncodingDetectionResult(
                    encoding=selected_encoding,
                    confidence="medium",
                    detection_method="heuristic",
                    bom_present=False,
                    candidates=("cp949", "euc-kr"),
                    evidence=evidence,
                )

            if len(candidate_results) > 1 and best_score <= 0:
                raise AmbiguousEncodingError(
                    "Multiple encodings decode this sample but no language-specific evidence is strong enough to prefer one",
                    candidates=tuple(item[0] for item in candidate_results),
                )

            encoding, _, _, _ = candidate_results[0]
            return EncodingDetectionResult(
                encoding=encoding,
                confidence="medium",
                detection_method="heuristic",
                bom_present=False,
                candidates=(encoding,),
                evidence=(f"Heuristic decode succeeded with {encoding}",),
            )

        raise EncodingNotDetectedError("No supported encoding could be determined")


def detect_encoding(raw_bytes: bytes) -> EncodingDetectionResult:
    return EncodingDetector().detect(raw_bytes)
