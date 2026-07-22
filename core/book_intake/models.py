from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .corruption_detector import TextQualityReport


@dataclass(frozen=True)
class SourceReadResult:
    source_path: Path
    filename: str
    extension: str
    byte_size: int
    raw_bytes: bytes


@dataclass(frozen=True)
class EncodingDetectionResult:
    encoding: str
    confidence: str
    detection_method: str
    bom_present: bool
    candidates: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class DecodedSource:
    encoding: str
    text: str
    byte_size: int
    character_count: int
    bom_removed: bool
    content_hash: str


@dataclass(frozen=True)
class LanguageDetectionResult:
    language: str
    confidence: int
    script_statistics: tuple[tuple[str, int], ...]
    recommended_profile: str
    summary: str


@dataclass(frozen=True)
class BookIntakeResult:
    """Immutable result produced by the Book Intake orchestration pipeline."""

    source_path: Path
    file_name: str
    file_size_bytes: int
    encoding: str
    encoding_confidence: str
    text: str
    text_length: int
    quality_report: TextQualityReport
    language_result: LanguageDetectionResult
    status: str
    recommended_action: str
    summary: str
