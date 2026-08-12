from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterBoundary:
    """Immutable chapter boundary mapping for RM-8.4 Reader Packaging Layer.

    Position units: Python Unicode string code-point offsets (0-based, end-exclusive).
    """

    chapter_id: str
    chapter_order: int
    chapter_title: str
    start_position: int
    end_position: int
    scene_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReaderChapterMap:
    """Immutable ordered chapter mapping container for RM-8.4 Reader Packaging Layer."""

    chapters: tuple[ChapterBoundary, ...]