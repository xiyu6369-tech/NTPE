from __future__ import annotations

import codecs
from pathlib import Path

from .models import InputFileInspection, LanguageDefinition, LanguageDetectionResult


MAX_SAMPLE_BYTES = 65_536

SOURCE_LANGUAGES = (
    LanguageDefinition("auto", "Automatic detection", True, True, "offline_detection"),
    LanguageDefinition("ko", "Korean", True, True, "integrated"),
    LanguageDefinition("ja", "Japanese", True, False, "not_yet_integrated"),
    LanguageDefinition("en", "English", True, False, "not_yet_integrated"),
)

TARGET_LANGUAGES = (
    LanguageDefinition("zh-Hant", "Traditional Chinese", True, True, "integrated"),
)


def source_languages() -> tuple[LanguageDefinition, ...]:
    return SOURCE_LANGUAGES


def target_languages() -> tuple[LanguageDefinition, ...]:
    return TARGET_LANGUAGES


def _count_signals(text: str) -> dict[str, int]:
    counts = {"hangul": 0, "hiragana": 0, "katakana": 0, "cjk": 0, "latin": 0}
    for character in text:
        codepoint = ord(character)
        if 0xAC00 <= codepoint <= 0xD7A3 or 0x1100 <= codepoint <= 0x11FF:
            counts["hangul"] += 1
        elif 0x3040 <= codepoint <= 0x309F:
            counts["hiragana"] += 1
        elif 0x30A0 <= codepoint <= 0x30FF or 0x31F0 <= codepoint <= 0x31FF:
            counts["katakana"] += 1
        elif 0x3400 <= codepoint <= 0x4DBF or 0x4E00 <= codepoint <= 0x9FFF:
            counts["cjk"] += 1
        elif 0x0041 <= codepoint <= 0x005A or 0x0061 <= codepoint <= 0x007A:
            counts["latin"] += 1
    return counts


def detect_source_language(text: str) -> LanguageDetectionResult:
    counts = _count_signals(text)
    signal_total = sum(counts.values())
    signals = tuple(f"{name}={counts[name]}" for name in ("hangul", "hiragana", "katakana", "cjk", "latin"))
    if signal_total == 0:
        return LanguageDetectionResult("unknown", 0.0, signals, len(text), True)

    hangul_ratio = counts["hangul"] / signal_total
    kana_count = counts["hiragana"] + counts["katakana"]
    kana_ratio = kana_count / signal_total
    latin_ratio = counts["latin"] / signal_total

    if counts["hangul"] >= 3 and hangul_ratio >= 0.30:
        confidence = min(0.99, 0.60 + hangul_ratio * 0.39)
        return LanguageDetectionResult("ko", round(confidence, 4), signals, len(text), False)
    if kana_count >= 2 and kana_ratio >= 0.08:
        confidence = min(0.99, 0.62 + kana_ratio * 0.37)
        return LanguageDetectionResult("ja", round(confidence, 4), signals, len(text), False)
    if counts["latin"] >= 5 and latin_ratio >= 0.60:
        confidence = min(0.99, 0.55 + latin_ratio * 0.44)
        return LanguageDetectionResult("en", round(confidence, 4), signals, len(text), False)
    return LanguageDetectionResult("unknown", 0.35, signals, len(text), True)


def _decode_sample(data: bytes, truncated: bool) -> tuple[str, str]:
    if data.startswith(codecs.BOM_UTF8):
        return data.decode("utf-8-sig"), "utf-8-sig"
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        return data.decode("utf-16"), "utf-16"
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    return decoder.decode(data, final=not truncated), "utf-8"


def inspect_text_file(path: str | Path, *, max_sample_bytes: int = MAX_SAMPLE_BYTES) -> InputFileInspection:
    input_path = Path(path)
    empty_detection = detect_source_language("")
    try:
        file_size = input_path.stat().st_size
        with input_path.open("rb") as stream:
            data = stream.read(max_sample_bytes + 1)
    except (OSError, ValueError) as exc:
        return InputFileInspection(
            str(input_path), input_path.name, 0, "unknown", False, False, 0, False,
            empty_detection, "無法讀取此檔案，請確認檔案存在且有讀取權限。",
        )

    truncated = len(data) > max_sample_bytes
    sample = data[:max_sample_bytes]
    try:
        text, encoding = _decode_sample(sample, truncated)
    except UnicodeError:
        return InputFileInspection(
            str(input_path), input_path.name, file_size, "unknown", False, True, len(sample), truncated,
            empty_detection, "無法讀取此檔案，可能是編碼不支援或內容已損壞。",
        )

    mojibake_markers = ("Ã", "Â", "â€™", "ï¿½", "�")
    suspected_mojibake = any(marker in text for marker in mojibake_markers)
    return InputFileInspection(
        str(input_path), input_path.name, file_size, encoding, True, suspected_mojibake,
        len(sample), truncated, detect_source_language(text), "",
    )
