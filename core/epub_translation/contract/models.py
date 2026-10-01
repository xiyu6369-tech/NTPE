"""EPUB Translation Contract Models — S1.

Immutable data models for EPUB translation pipeline.
All models are frozen dataclasses with deterministic validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from types import MappingProxyType


@dataclass(frozen=True)
class EpubMetadata:
    """EPUB metadata extracted from OPF/package.

    Immutable; mirrors the extraction layer's EpubMetadata.
    """
    title: str | None
    author: str | None
    language: str | None
    identifier: str | None
    publisher: str | None
    date: str | None
    raw: MappingProxyType[str, Any]


@dataclass(frozen=True)
class EpubChapterBoundary:
    """Chapter boundary from extraction layer.

    Position units: Python Unicode string code-point offsets (0-based, end-exclusive)
    in the extraction's `extracted_text` coordinate system.

    The `extracted_text` contains chapter markers:
        === CHAPTER {index}: {title} ===
        {chapter_body}
    \\n

    Therefore:
    - `start_offset` / `end_offset` are marker-inclusive ranges.
    - `body_start_offset` / `body_end_offset` are pure chapter body ranges.
      These may be unavailable (None) if extraction layer has not yet provided them.
      Contract consumers MUST NOT assume they equal start/end offsets.
    """

    index: int                          # 1-based, spine order
    spine_position: int                 # Original spine position (1-based)
    title: str | None                   # Extracted or fallback title
    source_href: str | None             # Normalized XHTML href (may contain fragment)
    start_offset: int                   # In extracted_text, marker-inclusive start
    end_offset: int                     # In extracted_text, marker-inclusive end
    is_linear: bool = True              # True = reading order, False = supplementary
    toc_level: int = 0                  # TOC nesting level
    word_count: int = 0                 # Pure body word count
    landmark_type: str | None = None    # cover, toc, etc.
    status: str = "linear"              # "linear" | "supplementary"
    body_start_offset: int | None = None    # Pure body start in extracted_text
    body_end_offset: int | None = None      # Pure body end in extracted_text

    def __post_init__(self) -> None:
        if self.body_start_offset is not None and self.body_end_offset is not None:
            if self.body_end_offset < self.body_start_offset:
                raise ValueError(
                    f"body_end_offset ({self.body_end_offset}) < body_start_offset ({self.body_start_offset})"
                )

    @property
    def chapter_id(self) -> str:
        """Deterministic chapter identifier.

        Uses spine position as primary key to distinguish duplicate titles.
        """
        return f"ch{self.spine_position:04d}"

    @property
    def fragment(self) -> str | None:
        """Extract fragment from source_href if present."""
        if not self.source_href:
            return None
        if "#" in self.source_href:
            return self.source_href.split("#", 1)[1]
        return None

    @property
    def href_without_fragment(self) -> str | None:
        """Source href without fragment."""
        if not self.source_href:
            return None
        if "#" in self.source_href:
            return self.source_href.split("#", 1)[0]
        return self.source_href


@dataclass(frozen=True)
class ResourceRef:
    """Resource reference (image, CSS, font, etc.) from extraction."""
    type: str
    href: str
    chapter_index: int | None
    metadata: MappingProxyType[str, Any]


@dataclass(frozen=True)
class TocEntry:
    """Table of contents entry from nav.xhtml or NCX."""
    href: str
    title: str
    level: int


@dataclass(frozen=True)
class ExtractionManifest:
    """Extraction metadata from EpubExtractionBoundary."""
    extractor_version: str
    extracted_at: str
    chapter_count: int
    total_characters: int
    total_words: int
    warnings: tuple[str, ...]
    resources: tuple[ResourceRef, ...]
    spine_item_count: int
    nav_toc_entries: int
    encoding_used: str
    parsing_duration_ms: int
    fixed_layout: MappingProxyType[str, Any] | None = None


@dataclass(frozen=True)
class EpubTranslationInput:
    """Complete input required for EPUB translation.

    Immutable; all collections use tuple for immutability.
    """

    source_epub_path: Path
    original_hash: str                    # SHA256 of original EPUB bytes
    extraction_status: str                # "success" | "partial" | "manual_review_required" | "blocked"
    warnings: tuple[str, ...]
    metadata: EpubMetadata
    chapter_map: tuple[EpubChapterBoundary, ...]
    resources: tuple[ResourceRef, ...]
    toc_entries: tuple[TocEntry, ...]
    fixed_layout_info: MappingProxyType[str, Any] | None
    extraction_manifest: ExtractionManifest | None = None

    def __post_init__(self) -> None:
        # Validate SHA256 format
        import re
        if not re.fullmatch(r"[0-9a-f]{64}", self.original_hash.lower()):
            raise ValueError(f"original_hash must be 64-char hex: {self.original_hash}")

    @property
    def linear_chapters(self) -> tuple[EpubChapterBoundary, ...]:
        """Chapters with is_linear=True in spine order."""
        return tuple(c for c in self.chapter_map if c.is_linear)

    @property
    def supplementary_chapters(self) -> tuple[EpubChapterBoundary, ...]:
        """Chapters with is_linear=False in spine order."""
        return tuple(c for c in self.chapter_map if not c.is_linear)


@dataclass(frozen=True)
class EpubTranslationChunk:
    """A single translation unit belonging to exactly one chapter.

    Invariants:
    - source_text is PURE chapter body text (no marker)
    - Chunk belongs to exactly one chapter (no cross-chapter chunks)
    - Empty chapter produces exactly one empty chunk
    """

    chunk_id: str
    chapter_id: str
    chapter_order: int
    chunk_sequence: int                   # 0-based within chapter
    source_text: str                      # Pure body text (marker-free)
    extracted_start_offset: int           # In extracted_text, chunk start
    extracted_end_offset: int             # In extracted_text, chunk end
    body_start_offset: int                # In extracted_text, body-relative start
    body_end_offset: int                  # In extracted_text, body-relative end
    source_href: str | None
    fragment: str | None

    def __post_init__(self) -> None:
        if self.chunk_sequence < 0:
            raise ValueError(f"chunk_sequence must be >= 0: {self.chunk_sequence}")
        if self.extracted_end_offset < self.extracted_start_offset:
            raise ValueError("extracted_end_offset must be >= extracted_start_offset")
        if self.body_end_offset < self.body_start_offset:
            raise ValueError("body_end_offset must be >= body_start_offset")

        body_range = self.body_end_offset - self.body_start_offset
        extracted_range = self.extracted_end_offset - self.extracted_start_offset

        # Empty body: body range is zero (valid for empty body chunks at any position)
        if body_range == 0:
            return

        # Invariant check: body range must equal extracted range
        if body_range != extracted_range:
            # Invariant violated - check which specific boundary is violated for error message
            if self.body_start_offset < self.extracted_start_offset:
                raise ValueError("body_start_offset must be >= extracted_start_offset")
            if self.body_end_offset > self.extracted_end_offset:
                raise ValueError("body_end_offset must be <= extracted_end_offset")
            # Fallback for other invariant violations
            raise ValueError("body range must equal extracted range")

        # Invariant holds - cross-coordinate "violations" are valid coordinate system differences
        # No further checks needed


@dataclass(frozen=True)
class EpubChunkResult:
    """Result of translating a single chunk."""

    chunk_id: str
    status: str                           # "success" | "failed" | "skipped" | "dry_run" | "incomplete"
    translated_text: str                  # Empty string on failure
    error: str | None
    attempt: int
    qa_report: MappingProxyType[str, Any] | None
    metadata: MappingProxyType[str, Any]

    VALID_STATUSES = frozenset({"success", "failed", "skipped", "dry_run", "incomplete"})

    def __post_init__(self) -> None:
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid chunk status: {self.status}")
        if self.attempt < 0:
            raise ValueError(f"attempt must be >= 0: {self.attempt}")


@dataclass(frozen=True)
class EpubChapterResult:
    """Aggregated result for a single chapter."""

    chapter_id: str
    chapter_order: int
    chunk_results: tuple[EpubChunkResult, ...]
    aggregate_status: str                 # "success" | "incomplete" | "failed"
    success_count: int
    failed_count: int
    skipped_count: int
    assembled_text: str                   # Concatenated successful chunks

    VALID_STATUSES = frozenset({"success", "incomplete", "failed"})

    def __post_init__(self) -> None:
        if self.aggregate_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid chapter aggregate status: {self.aggregate_status}")
        if self.success_count < 0 or self.failed_count < 0 or self.skipped_count < 0:
            raise ValueError("Counts must be >= 0")
        # Verify counts match actual chunk results
        actual_success = sum(1 for c in self.chunk_results if c.status == "success")
        actual_failed = sum(1 for c in self.chunk_results if c.status == "failed")
        actual_skipped = sum(1 for c in self.chunk_results if c.status == "skipped")
        actual_dry_run = sum(1 for c in self.chunk_results if c.status == "dry_run")
        if self.success_count != actual_success:
            raise ValueError(f"success_count mismatch: declared={self.success_count}, actual={actual_success}")
        if self.failed_count != actual_failed:
            raise ValueError(f"failed_count mismatch: declared={self.failed_count}, actual={actual_failed}")
        if self.skipped_count != actual_skipped:
            raise ValueError(f"skipped_count mismatch: declared={self.skipped_count}, actual={actual_skipped}")


@dataclass(frozen=True)
class EpubTranslationResult:
    """Complete EPUB translation result."""

    aggregate_status: str                 # "success" | "incomplete" | "failed"
    chapter_results: tuple[EpubChapterResult, ...]   # In spine order
    success_count: int
    failed_count: int
    skipped_count: int
    session_id: str
    resume_state_path: Path | None = None

    VALID_STATUSES = frozenset({"success", "incomplete", "failed"})

    def __post_init__(self) -> None:
        if self.aggregate_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid aggregate status: {self.aggregate_status}")
        if self.success_count < 0 or self.failed_count < 0 or self.skipped_count < 0:
            raise ValueError("Counts must be >= 0")

    @property
    def total_chapters(self) -> int:
        return len(self.chapter_results)

    @property
    def total_chunks(self) -> int:
        return sum(len(cr.chunk_results) for cr in self.chapter_results)

    @property
    def linear_chapter_results(self) -> tuple[EpubChapterResult, ...]:
        """Chapter results in spine order (linear only)."""
        return self.chapter_results