from __future__ import annotations

from .models import LanguageDetectionResult

# Unicode script ranges
_HANGUL_RANGES = [
    (0xAC00, 0xD7AF),   # Hangul Syllables
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x3130, 0x318F),   # Hangul Compatibility Jamo
]

_HIRAGANA_RANGE = (0x3040, 0x309F)

_KATAKANA_RANGE = (0x30A0, 0x30FF)

_CJK_RANGE = (0x4E00, 0x9FFF)

_LATIN_LOWER_RANGE = (0x0061, 0x007A)
_LATIN_UPPER_RANGE = (0x0041, 0x005A)

# Thresholds
_MIN_SCRIPT_RATIO = 0.60
_MIXED_RATIO = 0.30

# Confidence constants
_CONFIDENCE_PRIMARY = 95
_CONFIDENCE_MIXED = 70
_CONFIDENCE_UNKNOWN_MAX = 30


class SourceLanguageDetector:
    """Pure offline Unicode-script-based language detection.

    No AI, no network, no third-party libraries.
    """

    def detect(self, text: str) -> LanguageDetectionResult:
        """Analyse *text* and return a LanguageDetectionResult."""
        if not text or len(text.strip()) == 0:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0,
                script_statistics=(),
                recommended_profile="unknown",
                summary="Unable to determine language: empty input.",
            )

        # Count characters per script
        hangul_count = 0
        hiragana_count = 0
        katakana_count = 0
        cjk_count = 0
        latin_count = 0
        other_count = 0

        for ch in text:
            cp = ord(ch)
            if _in_any_range(cp, _HANGUL_RANGES):
                hangul_count += 1
            elif _in_range(cp, _HIRAGANA_RANGE):
                hiragana_count += 1
            elif _in_range(cp, _KATAKANA_RANGE):
                katakana_count += 1
            elif _in_range(cp, _CJK_RANGE):
                cjk_count += 1
            elif _is_latin_char(cp):
                latin_count += 1
            else:
                other_count += 1

        total = hangul_count + hiragana_count + katakana_count + cjk_count + latin_count + other_count

        # Build statistics tuple ordered deterministically
        stats_items: list[tuple[str, int]] = []
        if hangul_count > 0:
            stats_items.append(("hangul", hangul_count))
        if hiragana_count > 0:
            stats_items.append(("hiragana", hiragana_count))
        if katakana_count > 0:
            stats_items.append(("katakana", katakana_count))
        if cjk_count > 0:
            stats_items.append(("cjk", cjk_count))
        if latin_count > 0:
            stats_items.append(("latin", latin_count))
        if other_count > 0:
            stats_items.append(("other", other_count))
        script_statistics = tuple(stats_items)

        if total == 0:
            return LanguageDetectionResult(
                language="unknown",
                confidence=0,
                script_statistics=script_statistics,
                recommended_profile="unknown",
                summary="Unable to determine language: no detectable script characters.",
            )

        # ── Language identification ──────────────────────────────

        kana_count = hiragana_count + katakana_count
        has_kana = kana_count > 0
        has_hangul = hangul_count > 0
        has_cjk = cjk_count > 0
        has_latin = latin_count > 0

        # Japanese: core signal is presence of kana (unique to Japanese).
        # Japanese text naturally has both kana and CJK (kanji), so the "Japanese block"
        # is kana + CJK combined.
        ja_block = kana_count + cjk_count

        # Korean: core signal is hangul (unique to Korean).
        ko_block = hangul_count + cjk_count  # hanja fall into CJK range

        if has_kana:
            ja_ratio = ja_block / total
            # Also check that hangul is not a significant presence
            hangul_intrusion = hangul_count / total if total > 0 else 0.0

            if ja_ratio >= _MIN_SCRIPT_RATIO and hangul_intrusion < _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="ja",
                    confidence=_CONFIDENCE_PRIMARY,
                    script_statistics=script_statistics,
                    recommended_profile="ja-zh-Hant",
                    summary="Primary language: Japanese.",
                )

            # Mixed Japanese
            if ja_ratio >= _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="ja-zh-Hant",
                    summary=_build_mixed_summary("Japanese", script_statistics),
                )

            # Kana present but at very low ratio — still Japanese if no hangul
            if not has_hangul and ja_ratio > 0:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="ja-zh-Hant",
                    summary=_build_mixed_summary("Japanese", script_statistics),
                )

        if has_hangul:
            ko_ratio = ko_block / total
            kana_intrusion = kana_count / total if total > 0 else 0.0

            if ko_ratio >= _MIN_SCRIPT_RATIO and kana_intrusion < _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="ko",
                    confidence=_CONFIDENCE_PRIMARY,
                    script_statistics=script_statistics,
                    recommended_profile="ko-zh-Hant",
                    summary="Primary language: Korean.",
                )

            # Mixed Korean
            if ko_ratio >= _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="ko-zh-Hant",
                    summary=_build_mixed_summary("Korean", script_statistics),
                )

            # Hangul present but at low ratio — still Korean if no kana
            if not has_kana:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="ko-zh-Hant",
                    summary=_build_mixed_summary("Korean", script_statistics),
                )

        # Chinese detection — CJK without kana & without hangul
        if has_cjk and not has_kana and not has_hangul:
            zh_ratio = cjk_count / total

            if zh_ratio >= _MIN_SCRIPT_RATIO:
                return LanguageDetectionResult(
                    language="zh",
                    confidence=_CONFIDENCE_PRIMARY,
                    script_statistics=script_statistics,
                    recommended_profile="zh-Hant-zh-Hans",
                    summary="Primary language: Chinese.",
                )

            if zh_ratio >= _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="zh-Hant-zh-Hans",
                    summary=_build_mixed_summary("Chinese", script_statistics),
                )

            # CJK plus Latin — could be mixed ZH+EN
            if has_latin:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="zh-Hant-zh-Hans",
                    summary=_build_mixed_summary("Chinese", script_statistics),
                )

        # English detection
        if has_latin:
            latin_ratio = latin_count / total

            if latin_ratio >= _MIN_SCRIPT_RATIO:
                return LanguageDetectionResult(
                    language="en",
                    confidence=_CONFIDENCE_PRIMARY,
                    script_statistics=script_statistics,
                    recommended_profile="en-zh-Hant",
                    summary="Primary language: English.",
                )

            if latin_ratio >= _MIXED_RATIO:
                return LanguageDetectionResult(
                    language="mixed",
                    confidence=_CONFIDENCE_MIXED,
                    script_statistics=script_statistics,
                    recommended_profile="unknown",
                    summary="Mixed script composition: primarily Latin with other scripts.",
                )

        # Fallback: unknown
        return LanguageDetectionResult(
            language="unknown",
            confidence=_CONFIDENCE_UNKNOWN_MAX,
            script_statistics=script_statistics,
            recommended_profile="unknown",
            summary="Unable to determine language.",
        )


# ── helpers ──────────────────────────────────────────────────────


def _in_any_range(cp: int, ranges: list[tuple[int, int]]) -> bool:
    for lo, hi in ranges:
        if lo <= cp <= hi:
            return True
    return False


def _in_range(cp: int, r: tuple[int, int]) -> bool:
    lo, hi = r
    return lo <= cp <= hi


def _is_latin_char(cp: int) -> bool:
    return (
        _in_range(cp, _LATIN_LOWER_RANGE)
        or _in_range(cp, _LATIN_UPPER_RANGE)
    )


def _build_mixed_summary(primary_lang: str, stats: tuple[tuple[str, int], ...]) -> str:
    script_names = {name for name, _ in stats if name != "other"}
    languages: list[str] = []

    if "hangul" in script_names:
        languages.append("Korean")
    if "hiragana" in script_names or "katakana" in script_names:
        languages.append("Japanese")
    if "cjk" in script_names:
        languages.append("Chinese")
    if "latin" in script_names:
        languages.append("English")

    if languages:
        return f"Mixed {' and '.join(languages)}."
    return f"Mixed {primary_lang} and other scripts."