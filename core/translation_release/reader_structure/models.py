"""Compatibility re-export for legacy ``translation_release`` importers.

S13-07 moved the canonical definitions of ``ChapterBoundary`` and ``ReaderChapterMap``
to ``core.epub_translation.reader_models`` so that canonical EPUB production no longer
depends on the legacy ``translation_release`` namespace. This module re-exports the
canonical classes (single implementation, no duplicate definition) for the remaining
legacy delivery / reader_structure importers and legacy tests.
"""

from __future__ import annotations

from core.epub_translation.reader_models import ChapterBoundary, ReaderChapterMap

__all__ = ["ChapterBoundary", "ReaderChapterMap"]
