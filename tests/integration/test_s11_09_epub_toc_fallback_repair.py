"""S11-09 — EPUB TOC Fallback Minimal Production Repair regression.

Covers the S11-08-confirmed extraction defects in
``core/adapters/epub_extraction_boundary.py``:

  R1  standard EPUB 3 ``nav > ol > li`` TOC traversal
  R2  canonical manifest-href based TOC lookup (no empty ``spine_item["href"]`` key)
  R3  empty/whitespace TOC labels rejected in favour of the next title source

Unified precedence contract (authoritative repository behaviour):

  document h1 > document h2 > document <title> > nav/NCX TOC label > "Chapter N"

Separation is asserted: title fallback must not change spine order, ``chapter_id``,
linear semantics or resource mapping. Provider/network/real translation are 0; a
deterministic injected runtime is used only for the production-path packaging check.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from types import MappingProxyType
from xml.etree import ElementTree as ET

from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
from core.adapters.epub_extraction_boundary import (
    EpubExtractionBoundary,
    ExtractedTextIntakeRequest,
)
from core.epub_translation.chunking import ChunkingOptions, chunk_epub_translation_input
from core.epub_translation.contract import (
    EpubChapterBoundary,
    EpubChapterResult,
    EpubChunkResult,
    EpubMetadata,
    EpubTranslationInput,
    EpubTranslationResult,
    ResourceRef,
)
from core.epub_translation.reader_chapter_map import build_epub_reader_chapter_map_with_metadata
from core.epub_translation.runtime.epub_packager import (
    EpubPackagingInput,
    pack_epub_resource_aware,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""


def _make_epub(
    path: Path,
    chapters: list[tuple[str, str]],
    *,
    nav: str | None = None,
    ncx: str | None = None,
) -> Path:
    """Build a deterministic EPUB3/EPUB2 fixture.

    ``chapters`` is a list of ``(id, body_html)`` in spine order. ``nav``/``ncx``
    are raw inner markup for the respective navigation document, or ``None``.
    """
    items = "".join(
        f'<item id="{cid}" href="{cid}.xhtml" media-type="application/xhtml+xml"/>'
        for cid, _ in chapters
    )
    spine = "".join(f'<itemref idref="{cid}" linear="yes"/>' for cid, _ in chapters)
    nav_item = (
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        if nav is not None else ""
    )
    ncx_item = (
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        if ncx is not None else ""
    )
    spine_toc = ' toc="ncx"' if ncx is not None else ""

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>TOC Fallback Fixture</dc:title>
    <dc:identifier id="bookid">urn:uuid:s11-09-fixture</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>{nav_item}{ncx_item}{items}</manifest>
  <spine{spine_toc}>{spine}</spine>
</package>""",
        )
        if nav is not None:
            zf.writestr(
                "OEBPS/nav.xhtml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<html xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:epub="http://www.idpf.org/2007/ops"><body>'
                f"{nav}</body></html>",
            )
        if ncx is not None:
            zf.writestr(
                "OEBPS/toc.ncx",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
                '<head></head><docTitle><text>TOC Fallback Fixture</text></docTitle>'
                f"<navMap>{ncx}</navMap></ncx>",
            )
        for cid, body in chapters:
            zf.writestr(
                f"OEBPS/{cid}.xhtml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<html xmlns="http://www.w3.org/1999/xhtml"><head></head>'
                f"<body>{body}</body></html>",
            )
    return path


def _toc(*links: str) -> str:
    return f'<nav epub:type="toc"><h2>Contents</h2><ol>{"".join(links)}</ol></nav>'


def _extract(path: Path):
    return EpubExtractionBoundary().extract(path)


# ---------------------------------------------------------------------------
# Test A — EPUB3 nav label used when the chapter has no higher-priority title
# ---------------------------------------------------------------------------

def test_a_epub3_nav_label_used_as_fallback(tmp_path: Path) -> None:
    epub = _make_epub(
        tmp_path / "a.epub",
        [("ch1", "<p>body only</p>")],
        nav=_toc('<li><a href="ch1.xhtml">Chapter From Nav</a></li>'),
    )
    result = _extract(epub)

    assert result.chapter_map[0].title == "Chapter From Nav"
    assert result.extraction_manifest.nav_toc_entries == 1


# ---------------------------------------------------------------------------
# Test B — nav must not override a higher-priority document heading
# ---------------------------------------------------------------------------

def test_b_document_heading_outranks_nav_label(tmp_path: Path) -> None:
    epub = _make_epub(
        tmp_path / "b.epub",
        [("ch1", "<h1>Document Heading</h1><p>body</p>")],
        nav=_toc('<li><a href="ch1.xhtml">Different TOC Label</a></li>'),
    )
    result = _extract(epub)

    assert result.chapter_map[0].title == "Document Heading"


# ---------------------------------------------------------------------------
# Test C — NCX fallback (EPUB 2 path)
# ---------------------------------------------------------------------------

def test_c_ncx_label_used_as_fallback(tmp_path: Path) -> None:
    ncx = (
        '<navPoint id="n1"><navLabel><text>NCX Label One</text></navLabel>'
        '<content src="ch1.xhtml"/></navPoint>'
        '<navPoint id="n2"><navLabel><text>NCX Label Two</text></navLabel>'
        '<content src="ch2.xhtml"/></navPoint>'
    )
    epub = _make_epub(
        tmp_path / "c.epub",
        [("ch1", "<p>a</p>"), ("ch2", "<p>b</p>")],
        ncx=ncx,
    )
    result = _extract(epub)

    assert [c.title for c in result.chapter_map] == ["NCX Label One", "NCX Label Two"]
    assert result.extraction_manifest.nav_toc_entries == 2


# ---------------------------------------------------------------------------
# Test D — empty/whitespace label rejected
# ---------------------------------------------------------------------------

def test_d_whitespace_label_rejected(tmp_path: Path) -> None:
    epub = _make_epub(
        tmp_path / "d.epub",
        [("ch1", "<p>body</p>")],
        nav=_toc('<li><a href="ch1.xhtml">   \n\t  </a></li>'),
    )
    result = _extract(epub)

    title = result.chapter_map[0].title
    assert title == "Chapter 1"
    assert title is not None and title.strip() != ""


# ---------------------------------------------------------------------------
# Test E — no valid TOC source -> deterministic "Chapter N"
# ---------------------------------------------------------------------------

def test_e_missing_toc_source_uses_generated_title(tmp_path: Path) -> None:
    epub = _make_epub(tmp_path / "e.epub", [("ch1", "<p>a</p>"), ("ch2", "<p>b</p>")])
    result = _extract(epub)

    assert [c.title for c in result.chapter_map] == ["Chapter 1", "Chapter 2"]
    assert result.extraction_manifest.nav_toc_entries == 0


# ---------------------------------------------------------------------------
# Test F — href resolution: label maps to the correct chapter, fragment-safe
# ---------------------------------------------------------------------------

def test_f_toc_href_maps_to_correct_chapter(tmp_path: Path) -> None:
    # TOC order deliberately differs from spine order; ch2 entry carries a
    # fragment and an outer/inner nesting. The outer entry must survive and the
    # labels must attach to their own hrefs, not to TOC position.
    nav = _toc(
        '<li><a href="ch2.xhtml">Label For Two</a>'
        '<ol><li><a href="ch2.xhtml#s1">Section One</a></li></ol></li>',
        '<li><a href="ch1.xhtml">Label For One</a></li>',
    )
    epub = _make_epub(
        tmp_path / "f.epub",
        [("ch1", "<p>a</p>"), ("ch2", "<p>b</p>")],
        nav=nav,
    )
    result = _extract(epub)

    by_spine = {c.spine_position: c for c in result.chapter_map}
    assert by_spine[1].title == "Label For One"
    assert by_spine[2].title == "Label For Two"
    # spine order and identity are untouched by TOC order
    assert [c.source_href for c in result.chapter_map] == [
        "OEBPS/ch1.xhtml",
        "OEBPS/ch2.xhtml",
    ]
    assert [c.spine_position for c in result.chapter_map] == [1, 2]


# ---------------------------------------------------------------------------
# Production path — extraction -> title fallback -> real packaging -> nav.xhtml
# ---------------------------------------------------------------------------

def _extract_and_intake(epub_path: Path):
    result = EpubExtractionBoundary().extract(epub_path)
    request = ExtractedTextIntakeRequest(
        source_path=result.source_path,
        source_format="epub",
        extracted_text=result.extracted_text,
        original_file_hash=result.original_hash,
        extracted_text_hash=result.extracted_hash,
        epub_metadata=dict(result.metadata.raw) if result.metadata.raw else {},
        chapter_map=result.chapter_map,
        extraction_manifest=result.extraction_manifest,
        extractor_version=result.extraction_manifest.extractor_version,
        status=result.status,
        warnings=result.warnings,
    )
    intake = CanonicalBookIntakeAdapter().ingest_extracted(request)
    return result, intake


def _build_translation_input(epub_path: Path, result, intake) -> EpubTranslationInput:
    chapter_map = tuple(
        EpubChapterBoundary(
            index=c.index, spine_position=c.spine_position, title=c.title,
            source_href=c.source_href, start_offset=c.start_offset, end_offset=c.end_offset,
            is_linear=c.is_linear, word_count=c.word_count,
            body_start_offset=c.body_start_offset, body_end_offset=c.body_end_offset,
            landmark_type=c.landmark_type, status=c.status, toc_level=c.toc_level,
        )
        for c in (intake.chapter_map or ())
    )
    resources = tuple(
        ResourceRef(type=r.type, href=r.href, chapter_index=r.chapter_index,
                    metadata=MappingProxyType(dict(r.metadata)))
        for r in (intake.resource_refs or ())
    )
    md = intake.epub_metadata or {}
    return EpubTranslationInput(
        source_epub_path=epub_path,
        original_hash=result.original_hash,
        extraction_status=result.status,
        warnings=result.warnings,
        metadata=EpubMetadata(
            title=md.get("title"), author=md.get("author"), language=md.get("language"),
            identifier=md.get("identifier"), publisher=md.get("publisher"), date=md.get("date"),
            raw=MappingProxyType(dict(md.get("raw", {}))),
        ),
        chapter_map=chapter_map, resources=resources, toc_entries=(), fixed_layout_info=None,
    )


def _deterministic_runtime(options) -> EpubTranslationResult:
    by_chapter: dict[str, list] = {}
    for chunk in options.chunks:
        by_chapter.setdefault(chunk.chapter_id, []).append(chunk)

    chapter_results = []
    for order, chapter in enumerate(options.translation_input.chapter_map, start=1):
        chapter_chunks = sorted(by_chapter.get(chapter.chapter_id, []), key=lambda c: c.chunk_sequence)
        chunk_results = []
        texts = []
        for chunk in chapter_chunks:
            translated = f"[ZH:{chapter.chapter_id}] {chunk.source_text}"
            texts.append(translated)
            chunk_results.append(EpubChunkResult(
                chunk_id=chunk.chunk_id, status="success", translated_text=translated,
                error=None, attempt=1, qa_report=MappingProxyType({}),
                metadata=MappingProxyType({}),
            ))
        assembled = "\n\n".join(texts).strip()
        if assembled:
            assembled += "\n"
        chapter_results.append(EpubChapterResult(
            chapter_id=chapter.chapter_id, chapter_order=order,
            chunk_results=tuple(chunk_results), aggregate_status="success",
            success_count=len(chunk_results), failed_count=0, skipped_count=0,
            assembled_text=assembled,
        ))

    return EpubTranslationResult(
        aggregate_status="success",
        chapter_results=tuple(chapter_results),
        success_count=sum(c.success_count for c in chapter_results),
        failed_count=0,
        skipped_count=0,
        session_id="s11-09-deterministic",
        resume_state_path=None,
    )


def _read_nav_labels(path: Path) -> list[tuple[str, str]]:
    """Return [(href, label)] from the packaged nav.xhtml in document order."""
    with zipfile.ZipFile(path) as zf:
        nav_name = next(n for n in zf.namelist() if Path(n).name == "nav.xhtml")
        root = ET.fromstring(zf.read(nav_name))
    ns = {"xhtml": "http://www.w3.org/1999/xhtml"}
    links = root.findall(".//xhtml:nav//xhtml:a", ns)
    return [(a.get("href", ""), "".join(a.itertext()).strip()) for a in links]


def test_production_path_toc_fallback_reaches_final_nav(tmp_path: Path) -> None:
    nav = _toc(
        '<li><a href="ch1.xhtml">First From Nav</a></li>',
        '<li><a href="ch2.xhtml">Second From Nav</a></li>',
    )
    source = _make_epub(
        tmp_path / "prod.epub",
        [
            ("ch1", "<p>" + "first chapter prose. " * 40 + "</p>"),
            ("ch2", "<h1>Document H1 Two</h1><p>" + "second chapter prose. " * 40 + "</p>"),
        ],
        nav=nav,
    )

    result, intake = _extract_and_intake(source)
    # Extraction fallback is correct before packaging.
    assert [c.title for c in result.chapter_map] == ["First From Nav", "Document H1 Two"]

    ti = _build_translation_input(source, result, intake)
    assert [c.title for c in ti.chapter_map] == ["First From Nav", "Document H1 Two"]
    assert [c.chapter_id for c in ti.chapter_map] == ["ch0001", "ch0002"]

    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    translation_result = _deterministic_runtime(type("O", (), {"chunks": chunks, "translation_input": ti})())
    reader = build_epub_reader_chapter_map_with_metadata(
        translation_result=translation_result, translation_input=ti
    )

    output = tmp_path / "out" / "prod_zh.epub"
    output.parent.mkdir(parents=True, exist_ok=True)
    packaging = pack_epub_resource_aware(
        packaging_input=EpubPackagingInput(
            reader_chapter_map_result=reader,
            translation_input=ti,
            translation_result=translation_result,
        ),
        output_path=output,
    )
    assert packaging.success, packaging.validation_errors

    labels = _read_nav_labels(output)
    # ch1: nav fallback label survived to final navigation; ch2: document h1 wins.
    assert labels == [
        ("ch1.xhtml", "First From Nav"),
        ("ch2.xhtml", "Document H1 Two"),
    ]
