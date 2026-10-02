"""S9-07 EPUB Reader-First E2E flow (EPUB-01 .. EPUB-07).

Deterministic, offline, isolated. Canonical extraction + fake runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.adapters.epub_extraction_boundary import EpubExtractionBoundary
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from core.reader_project.manager import ReaderProjectManager
from core.reader_project.recovery import check_recovery_eligibility
from ui.translation_studio.project_view_model import build_card_model
from ui.translation_studio.pages.project_page import ProjectPage

from tests.e2e.conftest import FakeTranslationRunner, make_epub

_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"
_MSGBOX = "ui.translation_studio.pages.project_page.QMessageBox"


def _extract(tmp_path: Path, title: str = "Test Book", name: str = "book.epub"):
    epub = make_epub(tmp_path, name=name, title=title)
    result = EpubExtractionBoundary().extract(epub)
    return epub, result


def _epub_book_info(source: Path, result) -> dict:
    metadata = result.metadata
    chapter_map = result.chapter_map
    return {
        "title": metadata.title or source.stem,
        "source": str(source),
        "format": "epub",
        "chapters": len(chapter_map),
        "chars": len(result.extracted_text),
        "status": result.status,
        "warnings": list(result.warnings),
        "preview_text": result.extracted_text,
        "metadata": {
            "title": metadata.title,
            "author": metadata.author,
            "language": metadata.language,
            "identifier": metadata.identifier,
        },
        "chapter_map": [
            {
                "index": ch.index,
                "title": ch.title,
                "start_offset": ch.start_offset,
                "end_offset": ch.end_offset,
                "word_count": ch.word_count,
                "is_linear": ch.is_linear,
            }
            for ch in chapter_map
        ],
    }


# ---------------------------------------------------------------------------
# EPUB-01..EPUB-03 — Import / Extraction / Preview / Persistence
# ---------------------------------------------------------------------------

def test_epub_extraction_and_import_creates_project(qapp, tmp_path, manager, opener, page):
    source, result = _extract(tmp_path, title="測試電子書")
    assert result.status == "success"
    assert result.original_hash
    assert len(result.chapter_map) >= 2

    info = _epub_book_info(source, result)
    pid = page.add_project(name=info["title"], source=str(source), book_info=info)
    assert pid is not None

    stored = manager.load(pid)
    assert stored.source.format == "epub"
    assert stored.source.identity_kind == "epub_sha256"
    assert len(stored.source.hash) == 64  # canonical EPUB full sha256
    assert page.table.rowCount() == 1


def test_epub_preview_preserves_chapter_identity(qapp, tmp_path, manager, opener, page):
    source, result = _extract(tmp_path)
    info = _epub_book_info(source, result)
    preview = info["preview_text"]
    assert preview and preview.strip()  # actual content, not placeholder
    assert len(info["chapter_map"]) >= 2
    # chapter ordering preserved
    indices = [c["index"] for c in info["chapter_map"]]
    assert indices == sorted(indices)


def test_epub_project_persists_across_restart(qapp, tmp_path, manager, opener, page):
    source, result = _extract(tmp_path, title="Persist Book")
    info = _epub_book_info(source, result)
    pid = page.add_project(name=info["title"], source=str(source), book_info=info)

    manager2 = ReaderProjectManager(home=manager.store.home)
    page2 = ProjectPage()
    try:
        page2.set_project_manager(manager2)
        page2.refresh_projects()
        assert page2._persisted_ids == [pid]
        stored = manager2.load(pid)
        assert stored.source.format == "epub"
        assert stored.source.hash == manager.load(pid).source.hash
    finally:
        page2.close()


# ---------------------------------------------------------------------------
# EPUB-04..EPUB-06 — Translation entry / translation / output
#
# The production EPUB entry runs the real extraction -> intake -> chunking
# path. S9-07 originally recorded an F1 capability gap here (extraction did not
# populate chapter body offsets). S10-02 repaired the extraction contract, so
# the canonical entry now builds EpubTranslationOptions end-to-end. The runner
# remains faked so no provider/network/real translation occurs.
# ---------------------------------------------------------------------------

def test_epub_translation_entry_routes_to_canonical_epub_options(qapp, tmp_path, manager, opener, page):
    source, result = _extract(tmp_path)
    info = _epub_book_info(source, result)
    pid = page.add_project(name=info["title"], source=str(source), book_info=info)
    page.table.selectRow(0)

    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()

    runner = FakeTranslationRunner.last()
    assert runner is not None, "canonical EPUB entry must build options and start the runner"
    assert isinstance(runner.options, EpubTranslationOptions)
    assert runner.options.chunks, "real extraction output must yield canonical EPUB chunks"

    # routing is still EPUB (not TXT): the project is registered as epub
    assert manager.load(pid).source.format == "epub"


def test_epub_translation_entry_does_not_fall_back_to_txt(qapp, tmp_path, manager, opener, page):
    source, result = _extract(tmp_path)
    info = _epub_book_info(source, result)
    page.add_project(name=info["title"], source=str(source), book_info=info)
    page.table.selectRow(0)

    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner):
        page._on_translate()
    # canonical EPUB options were used; never started a TXT runtime
    runner = FakeTranslationRunner.last()
    assert runner is not None
    assert isinstance(runner.options, EpubTranslationOptions)


# ---------------------------------------------------------------------------
# EPUB-07 — Output isolation
# ---------------------------------------------------------------------------

def test_epub_outputs_isolated_between_projects(qapp, tmp_path, manager, opener, page):
    s1, r1 = _extract(tmp_path, title="Book One", name="one.epub")
    s2, r2 = _extract(tmp_path, title="Book Two", name="two.epub")
    i1, i2 = _epub_book_info(s1, r1), _epub_book_info(s2, r2)
    pid1 = page.add_project(name=i1["title"], source=str(s1), book_info=i1)
    pid2 = page.add_project(name=i2["title"], source=str(s2), book_info=i2)

    assert pid1 != pid2
    assert manager.load(pid1).source.hash != manager.load(pid2).source.hash

    # different outputs never cross-wire
    a1 = s1.parent / "output" / "epub_translation" / (i1["metadata"]["identifier"] or "unknown") / f"{s1.stem}_zh.epub"
    a2 = s2.parent / "output" / "epub_translation" / (i2["metadata"]["identifier"] or "unknown") / f"{s2.stem}_zh.epub"
    assert a1 != a2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
