from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from .corruption_detector import TextCorruptionDetector, TextQualityReport
from .decoder import decode_source
from .encoding_detector import EncodingDetector
from .language_detector import SourceLanguageDetector
from .models import (
    BookIntakeResult,
    DecodedSource,
    EncodingDetectionResult,
    LanguageDetectionResult,
    SourceReadResult,
)
from .source_reader import SourceFileReader


class _SourceReader(Protocol):
    def read(self, source_path: str | Path) -> SourceReadResult: ...


class _EncodingDetector(Protocol):
    def detect(self, raw_bytes: bytes) -> EncodingDetectionResult: ...


class _CorruptionDetector(Protocol):
    def analyze(self, text: str) -> TextQualityReport: ...


class _LanguageDetector(Protocol):
    def detect(self, text: str) -> LanguageDetectionResult: ...


Decoder = Callable[[bytes, EncodingDetectionResult], DecodedSource]

_QUALITY_STATUS_TO_INTAKE_STATUS = {
    "clean": "ready",
    "warning": "ready_with_warnings",
    "manual_review_required": "manual_review_required",
    "blocked": "blocked",
}

_STATUS_TO_ACTION = {
    "ready": "proceed",
    "ready_with_warnings": "proceed_with_warning",
    "manual_review_required": "manual_review",
    "blocked": "reject",
}

_LANGUAGE_NAMES = {
    "ko": "Korean",
    "ja": "Japanese",
    "zh": "Chinese",
    "en": "English",
}


class BookIntakeProcessor:
    """Orchestrate the deterministic, offline Book Intake components."""

    def __init__(
        self,
        source_reader: _SourceReader | None = None,
        encoding_detector: _EncodingDetector | None = None,
        decoder: Decoder | None = None,
        corruption_detector: _CorruptionDetector | None = None,
        language_detector: _LanguageDetector | None = None,
    ) -> None:
        self._source_reader = source_reader if source_reader is not None else SourceFileReader()
        self._encoding_detector = encoding_detector if encoding_detector is not None else EncodingDetector()
        self._decoder = decoder if decoder is not None else decode_source
        self._corruption_detector = (
            corruption_detector if corruption_detector is not None else TextCorruptionDetector()
        )
        self._language_detector = (
            language_detector if language_detector is not None else SourceLanguageDetector()
        )

    def process(self, source_path: str | Path) -> BookIntakeResult:
        """Process one source file without modifying it or writing output files."""
        source = self._source_reader.read(source_path)
        encoding = self._encoding_detector.detect(source.raw_bytes)
        decoded = self._decoder(source.raw_bytes, encoding)
        quality = self._corruption_detector.analyze(decoded.text)
        language = self._language_detector.detect(decoded.text)
        status = self._resolve_status(quality.status, language.language)
        return BookIntakeResult(
            source_path=source.source_path,
            file_name=source.filename,
            file_size_bytes=source.byte_size,
            encoding=decoded.encoding,
            encoding_confidence=encoding.confidence,
            text=decoded.text,
            text_length=decoded.character_count,
            quality_report=quality,
            language_result=language,
            status=status,
            recommended_action=_STATUS_TO_ACTION[status],
            summary=self._build_summary(status, decoded.encoding, language.language),
        )

    @staticmethod
    def _resolve_status(quality_status: str, language: str) -> str:
        status = _QUALITY_STATUS_TO_INTAKE_STATUS[quality_status]
        if status != "blocked" and language in {"unknown", "mixed"}:
            return "manual_review_required"
        return status

    @staticmethod
    def _build_summary(status: str, encoding: str, language: str) -> str:
        if status == "blocked":
            return "Book intake blocked because structural corruption was detected."
        if language == "unknown":
            return "Book intake requires manual review because the source language could not be determined."
        if language == "mixed":
            return "Book intake requires manual review because mixed source languages were detected."
        if status == "manual_review_required":
            return "Book intake requires manual review because text-quality findings were detected."
        if status == "ready_with_warnings":
            return "Book intake completed with warnings. Review text-quality findings before processing."
        language_name = _LANGUAGE_NAMES.get(language, language)
        return (
            f"Book intake completed. Encoding: {encoding.upper()}. "
            f"Source language: {language_name}. Ready for processing."
        )