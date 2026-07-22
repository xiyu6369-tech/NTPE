from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.book_intake import BookIntakeProcessor, BookIntakeResult
from core.book_intake.corruption_detector import Finding, TextQualityReport
from core.book_intake.errors import (
    AmbiguousEncodingError,
    DecodeFailedError,
    EmptyFileError,
    EncodingNotDetectedError,
    FileNotFoundError as SourceFileNotFoundError,
    FileTooLargeError,
    NotAFileError,
    UnsupportedExtensionError,
)
from core.book_intake.models import (
    DecodedSource,
    EncodingDetectionResult,
    LanguageDetectionResult,
    SourceReadResult,
)


def _process_text(tmp_path: Path, text: str, encoding: str = "utf-8") -> BookIntakeResult:
    path = tmp_path / "book.txt"
    path.write_bytes(text.encode(encoding))
    return BookIntakeProcessor().process(path)


class _BytesReader:
    def __init__(self, raw_bytes: bytes) -> None:
        self.raw_bytes = raw_bytes

    def read(self, source_path: str | Path) -> SourceReadResult:
        path = Path(source_path).resolve()
        return SourceReadResult(path, path.name, ".txt", len(self.raw_bytes), self.raw_bytes)


class _QualityDetector:
    def __init__(self, status: str) -> None:
        self.status = status

    def analyze(self, text: str) -> TextQualityReport:
        finding = () if self.status == "clean" else (Finding("test", "warning", 1, "test"),)
        return TextQualityReport(self.status, finding, 90, "test", "test")


class _LanguageDetector:
    def __init__(self, language: str) -> None:
        self.language = language

    def detect(self, text: str) -> LanguageDetectionResult:
        return LanguageDetectionResult(self.language, 95, (), "test", "test")


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("안녕하세요 한국어 소설입니다", "ko"),
        ("這是一段繁體中文小說內容", "zh"),
        ("これは日本語の小説です", "ja"),
        ("This is a complete English novel sentence.", "en"),
    ],
)
def test_utf8_languages_are_ready(tmp_path: Path, text: str, language: str) -> None:
    result = _process_text(tmp_path, text)
    assert result.status == "ready"
    assert result.language_result.language == language
    assert result.encoding == "utf-8"


def test_cp949_korean_is_ready(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "안녕하세요 한국어 소설입니다", "cp949")
    assert result.encoding == "cp949"
    assert result.language_result.language == "ko"
    assert result.status == "ready"


def test_shift_jis_japanese_is_ready(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "こんにちは日本語の小説です", "shift-jis")
    assert result.encoding == "shift-jis"
    assert result.language_result.language == "ja"
    assert result.status == "ready"


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be"])
def test_utf16_without_bom_uses_injected_reader(tmp_path: Path, encoding: str) -> None:
    text = "This is UTF sixteen text."
    processor = BookIntakeProcessor(source_reader=_BytesReader(text.encode(encoding)))
    result = processor.process(tmp_path / "book.txt")
    assert result.encoding == encoding
    assert result.text == text
    assert result.status == "ready"


@pytest.mark.parametrize(
    ("quality_status", "expected_status"),
    [
        ("clean", "ready"),
        ("warning", "ready_with_warnings"),
        ("manual_review_required", "manual_review_required"),
        ("blocked", "blocked"),
    ],
)
def test_quality_status_mapping(tmp_path: Path, quality_status: str, expected_status: str) -> None:
    path = tmp_path / "book.txt"
    path.write_text("This is English text.", encoding="utf-8")
    processor = BookIntakeProcessor(corruption_detector=_QualityDetector(quality_status))
    assert processor.process(path).status == expected_status


def test_unknown_language_requires_manual_review(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "12345 !!!")
    assert result.quality_report.status == "clean"
    assert result.language_result.language == "unknown"
    assert result.status == "manual_review_required"


def test_mixed_language_requires_manual_review(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "안녕하세요 こんにちは")
    assert result.language_result.language == "mixed"
    assert result.status == "manual_review_required"


def test_blocked_corruption_overrides_language(tmp_path: Path) -> None:
    path = tmp_path / "book.txt"
    path.write_text("12345", encoding="utf-8")
    processor = BookIntakeProcessor(corruption_detector=_QualityDetector("blocked"))
    result = processor.process(path)
    assert result.language_result.language == "unknown"
    assert result.status == "blocked"
    assert result.recommended_action == "reject"


@pytest.mark.parametrize(
    ("quality_status", "expected_action"),
    [
        ("clean", "proceed"),
        ("warning", "proceed_with_warning"),
        ("manual_review_required", "manual_review"),
        ("blocked", "reject"),
    ],
)
def test_recommended_action_mapping(tmp_path: Path, quality_status: str, expected_action: str) -> None:
    path = tmp_path / "book.txt"
    path.write_text("This is English text.", encoding="utf-8")
    processor = BookIntakeProcessor(corruption_detector=_QualityDetector(quality_status))
    assert processor.process(path).recommended_action == expected_action


def test_file_metadata_is_correct(tmp_path: Path) -> None:
    path = tmp_path / "小說.txt"
    raw_bytes = "這是一段小說內容".encode("utf-8")
    path.write_bytes(raw_bytes)
    result = BookIntakeProcessor().process(path)
    assert result.source_path == path.resolve()
    assert result.file_name == "小說.txt"
    assert result.file_size_bytes == len(raw_bytes)


def test_full_decoded_text_is_preserved(tmp_path: Path) -> None:
    text = ("第一章\n這是完整內容。\n" * 1000).rstrip()
    result = _process_text(tmp_path, text)
    assert result.text == text
    assert result.text_length == len(text)


def test_book_intake_result_is_immutable(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "This is English text.")
    with pytest.raises(FrozenInstanceError):
        result.status = "blocked"


def test_nested_results_are_immutable(tmp_path: Path) -> None:
    result = _process_text(tmp_path, "This is English text.")
    with pytest.raises(FrozenInstanceError):
        result.quality_report.status = "blocked"
    with pytest.raises(FrozenInstanceError):
        result.language_result.language = "unknown"


def test_dependency_injection_preserves_pipeline_order(tmp_path: Path) -> None:
    events: list[str] = []
    source = SourceReadResult((tmp_path / "book.txt").resolve(), "book.txt", ".txt", 5, b"hello")
    encoding = EncodingDetectionResult("utf-8", "high", "test", False, ("utf-8",), ())
    decoded = DecodedSource("utf-8", "hello", 5, 5, False, "hash")

    class Reader:
        def read(self, source_path: str | Path) -> SourceReadResult:
            events.append("read")
            return source

    class Encoding:
        def detect(self, raw_bytes: bytes) -> EncodingDetectionResult:
            events.append("encoding")
            return encoding

    def decoder(raw_bytes: bytes, detection: EncodingDetectionResult) -> DecodedSource:
        events.append("decode")
        return decoded

    class Quality:
        def analyze(self, text: str) -> TextQualityReport:
            events.append("quality")
            return TextQualityReport("clean", (), 100, "accept", "clean")

    class Language:
        def detect(self, text: str) -> LanguageDetectionResult:
            events.append("language")
            return LanguageDetectionResult("en", 95, (), "en-zh-Hant", "English")

    processor = BookIntakeProcessor(Reader(), Encoding(), decoder, Quality(), Language())
    assert processor.process(tmp_path / "book.txt").status == "ready"
    assert events == ["read", "encoding", "decode", "quality", "language"]


def test_file_not_found_propagates(tmp_path: Path) -> None:
    with pytest.raises(SourceFileNotFoundError):
        BookIntakeProcessor().process(tmp_path / "missing.txt")


def test_directory_rejection_propagates(tmp_path: Path) -> None:
    with pytest.raises(NotAFileError):
        BookIntakeProcessor().process(tmp_path)


def test_unsupported_extension_propagates(tmp_path: Path) -> None:
    path = tmp_path / "book.md"
    path.write_text("text", encoding="utf-8")
    with pytest.raises(UnsupportedExtensionError):
        BookIntakeProcessor().process(path)


def test_empty_file_propagates(tmp_path: Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")
    with pytest.raises(EmptyFileError):
        BookIntakeProcessor().process(path)


def test_oversized_file_propagates(tmp_path: Path) -> None:
    path = tmp_path / "large.txt"
    path.write_bytes(b"a" * (1024 * 1024 + 1))
    with pytest.raises(FileTooLargeError):
        BookIntakeProcessor().process(path)


def test_encoding_not_detected_propagates(tmp_path: Path) -> None:
    class Detector:
        def detect(self, raw_bytes: bytes) -> EncodingDetectionResult:
            raise EncodingNotDetectedError("not detected")

    path = tmp_path / "book.txt"
    path.write_text("text", encoding="utf-8")
    with pytest.raises(EncodingNotDetectedError):
        BookIntakeProcessor(encoding_detector=Detector()).process(path)


def test_ambiguous_encoding_propagates(tmp_path: Path) -> None:
    path = tmp_path / "book.txt"
    path.write_bytes(b"\xa1\xa1")
    with pytest.raises(AmbiguousEncodingError):
        BookIntakeProcessor().process(path)


def test_decoding_error_propagates(tmp_path: Path) -> None:
    def decoder(raw_bytes: bytes, detection: EncodingDetectionResult) -> DecodedSource:
        raise DecodeFailedError("decode failed")

    path = tmp_path / "book.txt"
    path.write_text("text", encoding="utf-8")
    with pytest.raises(DecodeFailedError):
        BookIntakeProcessor(decoder=decoder).process(path)


def test_repeated_execution_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "book.txt"
    path.write_text("This is deterministic English text.", encoding="utf-8")
    processor = BookIntakeProcessor()
    assert processor.process(path) == processor.process(path)


def test_processing_does_not_write_files(tmp_path: Path) -> None:
    path = tmp_path / "book.txt"
    path.write_text("This is English text.", encoding="utf-8")
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}
    original = path.read_bytes()
    BookIntakeProcessor().process(path)
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}
    assert after == before
    assert path.read_bytes() == original
