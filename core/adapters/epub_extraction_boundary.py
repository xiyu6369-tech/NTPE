from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EpubMetadata:
    title: str | None
    author: str | None
    language: str | None
    identifier: str | None
    publisher: str | None
    date: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class ChapterBoundary:
    index: int
    title: str | None
    start_offset: int
    end_offset: int
    source_href: str | None


@dataclass(frozen=True)
class ExtractionManifest:
    extractor_version: str
    extracted_at: str
    chapter_count: int
    total_characters: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EpubExtractionResult:
    source_path: Path
    original_hash: str
    extracted_text: str
    extracted_hash: str
    metadata: EpubMetadata
    chapter_map: tuple[ChapterBoundary, ...]
    extraction_manifest: ExtractionManifest
    status: str
    warnings: tuple[str, ...]


class EpubExtractionBoundary:
    """
    EPUB extraction boundary - architecture placeholder for P0 Stage 1.
    
    Actual EPUB extraction implementation is deferred to a later stage.
    This class defines the contract and provides a stub implementation
    that raises NotImplementedError.
    """

    def __init__(self):
        self.extractor_version = "epub-extraction-boundary-v0.1"

    def extract(self, epub_path: Path) -> EpubExtractionResult:
        raise NotImplementedError(
            "EPUB extraction is not implemented in P0 Stage 1. "
            "This boundary exists for architecture definition only. "
            "Implementation will be added in a subsequent stage."
        )

    def validate_epub(self, epub_path: Path) -> tuple[bool, str | None]:
        if not epub_path.exists():
            return False, f"EPUB file not found: {epub_path}"
        if epub_path.suffix.lower() != ".epub":
            return False, f"File is not an EPUB: {epub_path}"
        try:
            import ebooklib  # type: ignore[import-not-found]
            return True, None
        except ImportError:
            return False, "ebooklib not installed - EPUB extraction unavailable"