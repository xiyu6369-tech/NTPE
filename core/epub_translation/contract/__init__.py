"""EPUB Translation Contract — S1 Package."""

from .models import (
    EpubMetadata,
    EpubChapterBoundary,
    ResourceRef,
    TocEntry,
    ExtractionManifest,
    EpubTranslationInput,
    EpubTranslationChunk,
    EpubChunkResult,
    EpubChapterResult,
    EpubTranslationResult,
)

from .validation import (
    ContractValidationError,
    validate_sha256,
    validate_chapter_id,
    validate_epub_translation_input,
    validate_epub_translation_chunk,
    validate_epub_chunk_result,
    validate_epub_chapter_result,
    validate_epub_translation_result,
    validate_chunk_ownership,
    validate_complete_contract,
    validate_chapter_boundary,
)

__all__ = [
    # Models
    "EpubMetadata",
    "EpubChapterBoundary",
    "ResourceRef",
    "TocEntry",
    "ExtractionManifest",
    "EpubTranslationInput",
    "EpubTranslationChunk",
    "EpubChunkResult",
    "EpubChapterResult",
    "EpubTranslationResult",
    # Validation
    "ContractValidationError",
    "validate_sha256",
    "validate_chapter_id",
    "validate_epub_translation_input",
    "validate_epub_translation_chunk",
    "validate_epub_chunk_result",
    "validate_epub_chapter_result",
    "validate_epub_translation_result",
    "validate_chunk_ownership",
    "validate_complete_contract",
    "validate_chapter_boundary",
]