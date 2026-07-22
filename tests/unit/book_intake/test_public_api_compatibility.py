from __future__ import annotations

import importlib
import inspect

import core.book_intake as book_intake
from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
    EncodingDetector,
    SourceFileReader,
    SourceLanguageDetector,
    TextCorruptionDetector,
)
from core.book_intake.encoding_detector import EncodingDetector as ModuleEncodingDetector


def test_encoding_detector_is_the_original_public_class() -> None:
    assert EncodingDetector is not None
    assert EncodingDetector is ModuleEncodingDetector
    assert EncodingDetector.__module__ == "core.book_intake.encoding_detector"


def test_encoding_detector_public_export_is_unique_and_repeatable() -> None:
    assert book_intake.__all__.count("EncodingDetector") == 1
    assert importlib.import_module("core.book_intake").EncodingDetector is EncodingDetector


def test_existing_primary_public_api_remains_importable() -> None:
    public_api = (
        SourceFileReader,
        TextCorruptionDetector,
        SourceLanguageDetector,
        BookIntakeProcessor,
        BookPreflightAnalyzer,
        BookIntakeManifestBuilder,
    )
    assert all(item is not None for item in public_api)


def test_encoding_detector_contract_is_unchanged() -> None:
    assert str(inspect.signature(EncodingDetector)) == "() -> 'None'"
    assert str(inspect.signature(EncodingDetector.detect)) == (
        "(self, raw_bytes: 'bytes') -> 'EncodingDetectionResult'"
    )
