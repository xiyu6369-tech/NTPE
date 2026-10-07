"""S13-07 focused regression: canonical EPUB reader models split.

Proves that the canonical EPUB production package no longer depends on the legacy
``core.translation_release`` namespace, that ``ChapterBoundary`` / ``ReaderChapterMap``
have a single canonical definition, and that the legacy shim re-exports that single
definition (no second implementation).
"""

from __future__ import annotations

import dataclasses
import importlib
from pathlib import Path

import pytest

from core.epub_translation import reader_chapter_map
from core.epub_translation.reader_models import ChapterBoundary, ReaderChapterMap

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_EPUB_DIR = ROOT / "core" / "epub_translation"


def test_canonical_reader_chapter_map_binds_canonical_models() -> None:
    assert reader_chapter_map.ChapterBoundary is ChapterBoundary
    assert reader_chapter_map.ReaderChapterMap is ReaderChapterMap


def test_legacy_shim_reexports_single_canonical_definition() -> None:
    legacy = importlib.import_module("core.translation_release.reader_structure.models")
    assert legacy.ChapterBoundary is ChapterBoundary
    assert legacy.ReaderChapterMap is ReaderChapterMap


def test_canonical_epub_source_has_no_translation_release_import() -> None:
    offenders = []
    for path in CANONICAL_EPUB_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "core.translation_release" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_reader_models_contract_is_preserved() -> None:
    boundary = ChapterBoundary(
        chapter_id="c1",
        chapter_order=0,
        chapter_title="Chapter One",
        start_position=0,
        end_position=5,
        scene_ids=("s1",),
    )
    chapter_map = ReaderChapterMap(chapters=(boundary,))
    assert chapter_map.chapters == (boundary,)
    assert boundary.start_position == 0
    assert boundary.end_position == 5
    assert dataclasses.is_dataclass(boundary)
    assert boundary == ChapterBoundary("c1", 0, "Chapter One", 0, 5, ("s1",))
    with pytest.raises(dataclasses.FrozenInstanceError):
        boundary.chapter_id = "c2"  # type: ignore[misc]
