from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.book_intake import BookIntakeProcessor, BookIntakeResult
from core.book_intake.models import (
    BookIntakeResult as _BookIntakeResult,
    DecodedSource,
    EncodingDetectionResult,
    LanguageDetectionResult,
    SourceReadResult,
)
from core.book_intake.corruption_detector import TextCorruptionDetector, TextQualityReport
from core.book_intake.decoder import decode_source
from core.book_intake.encoding_detector import EncodingDetector
from core.book_intake.language_detector import SourceLanguageDetector
from core.adapters.epub_extraction_boundary import (
    ChapterBoundary,
    EpubExtractionError,
    EpubMetadata,
    ExtractionManifest,
    ExtractedTextIntakeRequest,
    ResourceRef,
)


@dataclass(frozen=True)
class SourceIdentity:
    source_path: Path
    source_hash: str
    file_size: int
    modified_time: float


@dataclass(frozen=True)
class CanonicalIntakeRequest:
    source_path: Path
    source_identity: SourceIdentity


@dataclass(frozen=True)
class CanonicalIntakeResult:
    intake_result: BookIntakeResult
    source_identity: SourceIdentity
    status: str
    warnings: tuple[str, ...]
    submission_eligible: bool
    epub_metadata: dict[str, Any] | None = None
    chapter_map: tuple[ChapterBoundary, ...] | None = None
    resource_refs: tuple[ResourceRef, ...] | None = None
    extraction_manifest: ExtractionManifest | None = None
    extraction_provenance: dict[str, Any] | None = None


class _ExtractedTextSourceReader:
    def __init__(self, extracted_text: str, source_path: Path, original_hash: str):
        self._extracted_text = extracted_text
        self._source_path = source_path
        self._original_hash = original_hash

    def read(self, source_path: str | Path) -> SourceReadResult:
        raw_bytes = self._extracted_text.encode("utf-8")
        return SourceReadResult(
            source_path=self._source_path,
            filename=self._source_path.name,
            extension=".txt",
            byte_size=len(raw_bytes),
            raw_bytes=raw_bytes,
        )


class _ExtractedTextEncodingDetector:
    def detect(self, raw_bytes: bytes) -> EncodingDetectionResult:
        return EncodingDetectionResult(
            encoding="utf-8",
            confidence="high",
            detection_method="known",
            bom_present=False,
            candidates=("utf-8",),
            evidence=("Pre-extracted text is known UTF-8",),
        )


class CanonicalBookIntakeAdapter:
    def __init__(self, processor: BookIntakeProcessor | None = None):
        self.processor = processor or BookIntakeProcessor()

    def process(self, request: CanonicalIntakeRequest) -> CanonicalIntakeResult:
        intake_result = self.processor.process(request.source_path)

        status = intake_result.status
        warnings: list[str] = []

        if intake_result.quality_report.status == "warning":
            warnings.append("Text quality warnings detected during intake")
        if intake_result.language_result.language in ("unknown", "mixed"):
            warnings.append(f"Language detection uncertain: {intake_result.language_result.language}")

        submission_eligible = status in ("ready", "ready_with_warnings")

        return CanonicalIntakeResult(
            intake_result=intake_result,
            source_identity=request.source_identity,
            status=status,
            warnings=tuple(warnings),
            submission_eligible=submission_eligible,
        )

    def process_path(self, source_path: Path) -> CanonicalIntakeResult:
        import hashlib
        stat = source_path.stat()
        content = source_path.read_bytes()
        source_hash = hashlib.sha256(content).hexdigest()[:16]
        source_identity = SourceIdentity(
            source_path=source_path,
            source_hash=source_hash,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )
        return self.process(CanonicalIntakeRequest(source_path=source_path, source_identity=source_identity))

    def ingest_extracted(self, request: ExtractedTextIntakeRequest) -> CanonicalIntakeResult:
        if request.status == "blocked":
            raise EpubExtractionError(
                f"EPUB extraction blocked: {', '.join(request.warnings)}",
                blocked=True,
                warnings=request.warnings,
            )

        if request.status == "manual_review_required":
            raise EpubExtractionError(
                f"EPUB extraction requires manual review: {', '.join(request.warnings)}",
                blocked=False,
                warnings=request.warnings,
            )

        source_identity = SourceIdentity(
            source_path=request.source_path,
            source_hash=request.original_file_hash[:16],
            file_size=len(request.extracted_text.encode("utf-8")),
            modified_time=request.source_path.stat().st_mtime if request.source_path.exists() else 0.0,
        )

        epub_metadata = {
            "title": request.epub_metadata.get("title"),
            "author": request.epub_metadata.get("author"),
            "language": request.epub_metadata.get("language"),
            "identifier": request.epub_metadata.get("identifier"),
            "publisher": request.epub_metadata.get("publisher"),
            "date": request.epub_metadata.get("date"),
            "raw": request.epub_metadata.get("raw", {}),
        }

        custom_processor = BookIntakeProcessor(
            source_reader=_ExtractedTextSourceReader(
                request.extracted_text, request.source_path, request.original_file_hash
            ),
            encoding_detector=_ExtractedTextEncodingDetector(),
            decoder=decode_source,
            corruption_detector=TextCorruptionDetector(),
            language_detector=SourceLanguageDetector(),
        )

        intake_result = custom_processor.process(request.source_path)

        status = intake_result.status
        warnings: list[str] = list(request.warnings)

        if intake_result.quality_report.status == "warning":
            warnings.append("Text quality warnings detected during intake")
        if intake_result.language_result.language in ("unknown", "mixed"):
            warnings.append(f"Language detection uncertain: {intake_result.language_result.language}")

        submission_eligible = status in ("ready", "ready_with_warnings")

        extraction_provenance = {
            "extractor_version": request.extractor_version,
            "extracted_text_hash": request.extracted_text_hash,
            "extraction_status": request.status,
            "original_file_hash": request.original_file_hash,
        }

        return CanonicalIntakeResult(
            intake_result=intake_result,
            source_identity=source_identity,
            status=status,
            warnings=tuple(warnings),
            submission_eligible=submission_eligible,
            epub_metadata=epub_metadata,
            chapter_map=request.chapter_map,
            resource_refs=request.extraction_manifest.resources,
            extraction_manifest=request.extraction_manifest,
            extraction_provenance=extraction_provenance,
        )