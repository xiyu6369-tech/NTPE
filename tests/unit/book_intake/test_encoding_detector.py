from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from core.book_intake.decoder import decode_source
from core.book_intake.encoding_detector import detect_encoding
from core.book_intake.errors import (
    AmbiguousEncodingError,
    DecodeFailedError,
    EncodingNotDetectedError,
    UnsupportedEncodingError,
)
from core.book_intake.models import DecodedSource, EncodingDetectionResult


def test_detects_utf8_ascii() -> None:
    result = detect_encoding(b"hello")
    assert result.encoding == "utf-8"
    assert result.confidence == "high"
    assert result.bom_present is False
    assert result.detection_method == "strict"


def test_detects_utf8_korean() -> None:
    data = "한글".encode("utf-8")
    result = detect_encoding(data)
    assert result.encoding == "utf-8"
    assert result.confidence == "high"


def test_detects_utf8_bom() -> None:
    data = "한글".encode("utf-8-sig")
    result = detect_encoding(data)
    assert result.encoding == "utf-8"
    assert result.bom_present is True
    assert result.detection_method == "bom"


def test_detects_utf16_le_bom() -> None:
    data = "漢字".encode("utf-16")
    result = detect_encoding(data)
    assert result.encoding == "utf-16-le"
    assert result.bom_present is True
    assert result.detection_method == "bom"


def test_detects_utf16_be_bom() -> None:
    data = b"\xfe\xff" + "漢字".encode("utf-16-be")
    result = detect_encoding(data)
    assert result.encoding == "utf-16-be"
    assert result.bom_present is True
    assert result.detection_method == "bom"


def test_detects_cp949_korean() -> None:
    data = "한글".encode("cp949")
    result = detect_encoding(data)
    assert result.encoding == "cp949"
    assert result.confidence == "medium"
    assert "cp949" in result.candidates
    assert "euc-kr" in result.candidates


def test_detects_euc_kr_sample() -> None:
    data = "한글".encode("euc-kr")
    result = detect_encoding(data)
    assert result.encoding == "cp949"
    assert result.confidence == "medium"
    assert "cp949" in result.candidates
    assert "euc-kr" in result.candidates


def test_detects_shift_jis_japanese() -> None:
    data = "こんにちは".encode("shift-jis")
    result = detect_encoding(data)
    assert result.encoding == "shift-jis"
    assert result.confidence == "medium"


def test_detects_utf16_le_without_bom() -> None:
    data = "abc".encode("utf-16-le")
    result = detect_encoding(data)
    assert result.encoding == "utf-16-le"
    assert result.bom_present is False


def test_detects_utf16_be_without_bom() -> None:
    data = "abc".encode("utf-16-be")
    result = detect_encoding(data)
    assert result.encoding == "utf-16-be"
    assert result.bom_present is False


def test_utf8_is_not_misdetected_as_utf16() -> None:
    data = b"hello"
    result = detect_encoding(data)
    assert result.encoding == "utf-8"


def test_shift_jis_is_not_misdetected_as_utf16() -> None:
    data = "日本語".encode("shift-jis")
    result = detect_encoding(data)
    assert result.encoding == "shift-jis"


def test_raises_when_encoding_cannot_be_determined() -> None:
    with pytest.raises(EncodingNotDetectedError):
        detect_encoding(b"\x00\x00\x00\x00")


def test_ambiguous_bytes_raise_ambiguous_encoding_error() -> None:
    with pytest.raises(AmbiguousEncodingError) as exc_info:
        detect_encoding(b"\xa1\xa1")

    assert "cp949" in exc_info.value.candidates
    assert "euc-kr" in exc_info.value.candidates


def test_detection_is_deterministic() -> None:
    data = "abc".encode("utf-8")
    first = detect_encoding(data)
    second = detect_encoding(data)
    assert first == second


def test_detection_result_is_immutable() -> None:
    result = detect_encoding(b"hello")
    assert is_dataclass(result)
    with pytest.raises((AttributeError, TypeError)):
        result.encoding = "utf-16-le"


def test_bom_takes_priority_over_heuristics() -> None:
    data = b"\xef\xbb\xbfabc"
    result = detect_encoding(data)
    assert result.encoding == "utf-8"
    assert result.detection_method == "bom"


def test_ambiguous_candidate_preserves_candidates() -> None:
    result = detect_encoding("한글".encode("cp949"))
    assert result.encoding == "cp949"
    assert result.candidates == ("cp949", "euc-kr")
    assert any("Ambiguity" in evidence for evidence in result.evidence)


def test_decoder_returns_decoded_source() -> None:
    detection = detect_encoding("한글".encode("utf-8"))
    decoded = decode_source(b"hello", detection)
    assert isinstance(decoded, DecodedSource)
    assert decoded.encoding == "utf-8"
    assert decoded.text == "hello"
    assert decoded.byte_size == 5
    assert decoded.character_count == 5
    assert decoded.bom_removed is False


def test_decoder_rejects_unsupported_encoding() -> None:
    result = detect_encoding(b"hello")
    with pytest.raises(UnsupportedEncodingError):
        decode_source(b"hello", result, encoding="latin-1")
