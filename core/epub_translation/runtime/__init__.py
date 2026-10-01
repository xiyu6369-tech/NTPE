"""S3 EPUB Translation Runtime — Canonical Runtime Integration.

Integration layer that routes S2 EpubTranslationChunk objects through
the existing canonical translation runtime without duplicating any
translation semantics, provider logic, quality gates, retry/recovery,
or memory systems.
"""

from __future__ import annotations

from .adapter import (
    translate_epub_translation_input,
    EpubTranslationOptions,
)

__all__ = [
    "translate_epub_translation_input",
    "EpubTranslationOptions",
]