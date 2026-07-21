from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from core.book_intake.decoder import decode_source
from core.book_intake.encoding_detector import detect_encoding
from core.book_intake.errors import DecodeFailedError, UnsupportedEncodingError


def test_utf8_decodes_normally() -> None:
    detection = detect_encoding(b"hello")
    decoded = decode_source(b"hello", detection)
    assert decoded.text == "hello"
    assert decoded.byte_size == 5
    assert decoded.character_count == 5


def test_utf8_bom_is_removed() -> None:
    detection = detect_encoding(b"\xef\xbb\xbfhello")
    decoded = decode_source(b"\xef\xbb\xbfhello", detection)
    assert decoded.text == "hello"
    assert decoded.bom_removed is True


def test_utf16_le_and_be_decode() -> None:
    detection = detect_encoding("漢字".encode("utf-16"))
    decoded = decode_source("漢字".encode("utf-16"), detection)
    assert decoded.text == "漢字"
    assert decoded.encoding == "utf-16-le"

    be_detection = detect_encoding(b"\xfe\xff" + "漢字".encode("utf-16-be"))
    be_decoded = decode_source(b"\xfe\xff" + "漢字".encode("utf-16-be"), be_detection)
    assert be_decoded.text == "漢字"
    assert be_decoded.encoding == "utf-16-be"


def test_cp949_decodes() -> None:
    detection = detect_encoding("한글".encode("cp949"))
    decoded = decode_source("한글".encode("cp949"), detection)
    assert decoded.text == "한글"


def test_shift_jis_decodes() -> None:
    detection = detect_encoding("日本語".encode("shift-jis"))
    decoded = decode_source("日本語".encode("shift-jis"), detection)
    assert decoded.text == "日本語"


def test_strict_decode_failure() -> None:
    from core.book_intake.models import EncodingDetectionResult

    detection = EncodingDetectionResult(
        encoding="utf-8",
        confidence="high",
        detection_method="strict",
        bom_present=False,
        candidates=("utf-8",),
        evidence=("direct",),
    )
    with pytest.raises(DecodeFailedError):
        decode_source(b"\x80", detection)


def test_replacement_character_is_rejected() -> None:
    detection = detect_encoding(b"hello")
    with pytest.raises(DecodeFailedError):
        decode_source(b"\x80", detection, encoding="utf-8", strict=True)


def test_hash_is_deterministic() -> None:
    detection = detect_encoding(b"hello")
    decoded = decode_source(b"hello", detection)
    assert decoded.content_hash == decoded.content_hash


def test_decoded_result_is_immutable() -> None:
    detection = detect_encoding(b"hello")
    decoded = decode_source(b"hello", detection)
    assert is_dataclass(decoded)
    with pytest.raises((AttributeError, TypeError)):
        decoded.text = "bye"


def test_unsupported_encoding_is_blocked() -> None:
    detection = detect_encoding(b"hello")
    with pytest.raises(UnsupportedEncodingError):
        decode_source(b"hello", detection, encoding="latin-1")
