"""S10-02 — EPUB extraction/intake contract repair: focused tests.

Deterministic, offline, isolated. No provider, no network, no real translation.
Covers:
  * chapter body offsets (populated, exact slice, multi-chapter ordering)
  * extraction -> intake metadata fidelity
  * positive real extraction -> intake -> canonical chunking integration
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from types import MappingProxyType

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
from core.adapters.epub_extraction_boundary import (
    EpubExtractionBoundary,
    ExtractedTextIntakeRequest,
)
from core.epub_translation.chunking import ChunkingOptions, chunk_epub_translation_input
from core.epub_translation.contract import (
    EpubChapterBoundary,
    EpubMetadata,
    EpubTranslationInput,
    ResourceRef,
)

_TITLE = "Repair Fixture Book"
_AUTHOR = "Fixture Author"
_LANGUAGE = "en"
_IDENTIFIER = "urn:uuid:s10-02-fixture"


def _make_epub(tmp_path: Path, name: str = "fixture.epub") -> Path:
    """Deterministic EPUB3: metadata, 2 chapters, spine, nav TOC, one resource."""
    epub_path = tmp_path / name
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{_TITLE}</dc:title>
    <dc:creator>{_AUTHOR}</dc:creator>
    <dc:language>{_LANGUAGE}</dc:language>
    <dc:identifier id="bookid">{_IDENTIFIER}</dc:identifier>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="img" href="img.png" media-type="image/png"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
  </spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body><nav epub:type="toc"><ol>
    <li><a href="ch1.xhtml">Chapter One</a></li>
    <li><a href="ch2.xhtml">Chapter Two</a></li>
  </ol></nav></body>
</html>""",
        )
        zf.writestr(
            "OEBPS/ch1.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter One</title></head>
<body><h1>Chapter One</h1><p>This is the first paragraph of the book.</p>
<p>This is the second paragraph of the book.</p></body></html>""",
        )
        zf.writestr(
            "OEBPS/ch2.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter Two</title></head>
<body><h1>Chapter Two</h1><p>This is chapter two content of the book.</p></body></html>""",
        )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\n")
    return epub_path


def _extract(tmp_path: Path):
    return EpubExtractionBoundary().extract(_make_epub(tmp_path))


def _intake(extraction_result):
    request = ExtractedTextIntakeRequest(
        source_path=extraction_result.source_path,
        source_format="epub",
        extracted_text=extraction_result.extracted_text,
        original_file_hash=extraction_result.original_hash,
        extracted_text_hash=extraction_result.extracted_hash,
        # Production call sites pass the namespaced raw metadata dict verbatim.
        epub_metadata=dict(extraction_result.metadata.raw) if extraction_result.metadata.raw else {},
        chapter_map=extraction_result.chapter_map,
        extraction_manifest=extraction_result.extraction_manifest,
        extractor_version=extraction_result.extraction_manifest.extractor_version,
        status=extraction_result.status,
        warnings=extraction_result.warnings,
    )
    return CanonicalBookIntakeAdapter().ingest_extracted(request)


def _build_translation_input(epub_path, extraction_result, intake_result):
    chapter_map = tuple(
        EpubChapterBoundary(
            index=cb.index,
            spine_position=cb.spine_position,
            title=cb.title,
            source_href=cb.source_href,
            start_offset=cb.start_offset,
            end_offset=cb.end_offset,
            is_linear=cb.is_linear,
            word_count=cb.word_count,
            body_start_offset=cb.body_start_offset,
            body_end_offset=cb.body_end_offset,
            landmark_type=cb.landmark_type,
            status=cb.status,
            toc_level=cb.toc_level,
        )
        for cb in (intake_result.chapter_map or ())
    )
    resources = tuple(
        ResourceRef(
            type=rr.type,
            href=rr.href,
            chapter_index=rr.chapter_index,
            metadata=MappingProxyType(dict(rr.metadata)),
        )
        for rr in (intake_result.resource_refs or ())
    )
    md = intake_result.epub_metadata or {}
    return EpubTranslationInput(
        source_epub_path=epub_path,
        original_hash=extraction_result.original_hash,
        extraction_status=extraction_result.status,
        warnings=extraction_result.warnings,
        metadata=EpubMetadata(
            title=md.get("title"),
            author=md.get("author"),
            language=md.get("language"),
            identifier=md.get("identifier"),
            publisher=md.get("publisher"),
            date=md.get("date"),
            raw=MappingProxyType(dict(md.get("raw", {}))),
        ),
        chapter_map=chapter_map,
        resources=resources,
        toc_entries=(),
        fixed_layout_info=None,
    )


# ---------------------------------------------------------------------------
# Chapter body offsets
# ---------------------------------------------------------------------------

def test_body_offsets_populated_and_slice_correct(tmp_path):
    result = _extract(tmp_path)
    text = result.extracted_text

    assert len(result.chapter_map) >= 2
    for ch in result.chapter_map:
        body_start = ch.body_start_offset
        body_end = ch.body_end_offset
        assert body_start is not None and body_end is not None

        marker = f"=== CHAPTER {ch.index}: {ch.title or 'Untitled'} ===\n"
        # marker-inclusive start still points at the marker
        assert text[ch.start_offset:ch.start_offset + len(marker)] == marker
        # body start is exactly after the marker
        assert body_start == ch.start_offset + len(marker)
        # body end is exactly at the trailing newline (outside the body)
        assert body_end == ch.end_offset - 1

        # invariants
        assert ch.start_offset <= body_start < body_end <= ch.end_offset

        body = text[body_start:body_end]
        assert body.strip()
        assert "=== CHAPTER" not in body
        # slice is the pure chapter body (marker- and trailing-newline-free)
        assert text[ch.start_offset:ch.end_offset] == marker + body + "\n"


def test_multi_chapter_offsets_ordered_non_overlapping_and_deterministic(tmp_path):
    result = _extract(tmp_path)
    chapters = result.chapter_map
    assert len(chapters) >= 2

    for prev, cur in zip(chapters, chapters[1:]):
        prev_body_end = prev.body_end_offset
        cur_body_start = cur.body_start_offset
        assert prev_body_end is not None and cur_body_start is not None
        assert prev_body_end <= cur_body_start
        # canonical extraction emits no gap between chapters
        assert prev.end_offset == cur.start_offset

    # determinism: re-extract the same bytes -> identical offsets
    second = _extract(tmp_path)
    assert [
        (c.start_offset, c.end_offset, c.body_start_offset, c.body_end_offset)
        for c in result.chapter_map
    ] == [
        (c.start_offset, c.end_offset, c.body_start_offset, c.body_end_offset)
        for c in second.chapter_map
    ]


# ---------------------------------------------------------------------------
# Metadata handoff
# ---------------------------------------------------------------------------

def test_metadata_preserved_through_intake(tmp_path):
    result = _extract(tmp_path)
    assert result.metadata.title == _TITLE

    intake = _intake(result)
    metadata = intake.epub_metadata
    assert metadata is not None
    assert metadata["title"] == _TITLE
    assert metadata["author"] == _AUTHOR
    assert metadata["language"] == _LANGUAGE
    assert metadata["identifier"] == _IDENTIFIER
    # provenance preserved
    assert metadata["raw"]


# ---------------------------------------------------------------------------
# Positive production path: extraction -> intake -> canonical chunking
# ---------------------------------------------------------------------------

def test_positive_extraction_intake_chunking_integration(tmp_path):
    epub_path = _make_epub(tmp_path)
    result = EpubExtractionBoundary().extract(epub_path)
    intake = _intake(result)
    assert intake.submission_eligible

    translation_input = _build_translation_input(epub_path, result, intake)
    chunks = chunk_epub_translation_input(
        translation_input, result.extracted_text, ChunkingOptions(chunk_size=1000)
    )

    assert chunks, "real extraction output must yield canonical EPUB chunks"

    by_chapter = {}
    for chunk in chunks:
        assert chunk.source_text
        assert "=== CHAPTER" not in chunk.source_text
        assert chunk.chapter_id in {c.chapter_id for c in translation_input.chapter_map}
        by_chapter.setdefault(chunk.chapter_id, []).append(chunk)

    assert set(by_chapter) == {c.chapter_id for c in translation_input.chapter_map}
    for chapter in translation_input.chapter_map:
        chapter_chunks = by_chapter[chapter.chapter_id]
        assert [c.chunk_sequence for c in chapter_chunks] == sorted(
            c.chunk_sequence for c in chapter_chunks
        )
        body_start = chapter.body_start_offset
        body_end = chapter.body_end_offset
        assert body_start is not None and body_end is not None
        body = result.extracted_text[body_start:body_end]
        for chunk in chapter_chunks:
            assert chunk.source_text in body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
