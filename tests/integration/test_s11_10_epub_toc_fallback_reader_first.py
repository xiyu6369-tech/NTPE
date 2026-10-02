"""S11-10 — EPUB TOC Fallback Reader-First E2E Verification.

Verification-only closure of the S11-08/S11-09 TOC fallback repair along the real
persisted reader-first path:

  source EPUB -> production extraction -> title derivation/TOC fallback
  -> canonical intake -> chunking -> deterministic injected translation
  -> real pack_epub_resource_aware -> persisted final EPUB (project-owned)
  -> fresh reopen / fresh project manager -> read final nav.xhtml
  -> reader-facing title/href verification.

The final ``nav.xhtml`` inside the persisted EPUB is the primary proof. Ordering,
identity, non-linear semantics and resource mapping are asserted separately and must
remain those locked by S11-03/S11-04 and S11-06/S11-07.

Title cases exercised by one deterministic 5-item fixture:

  item0 (linear)     Case A  nav fallback            -> "First From Nav"
  item1 (linear=no)  Case C  NCX fallback            -> "NCX Label One"
  item2 (linear)     Case B  document <h1> wins      -> "Document H1 Two"
  item3 (linear=no)  Case D  generated fallback      -> "Chapter 4"
  item4 (linear)     empty/whitespace nav label      -> "Chapter 5"

Source nav order (item2, item0, item4) deliberately differs from spine order.

Placement note: this verification lives under ``tests/integration`` rather than
``tests/e2e``. The shared Qt e2e session has a pre-existing, flaky Windows access
violation in ``test_s11_04``'s background TranslationRuntime thread; adding *any* new
e2e module perturbs that session and aborts the whole e2e directory run, independent of
this module's content. The full reader-first UI (ProjectPage) journey for this same
pipeline remains regression-locked by S10-03 and S11-07. This module therefore verifies
the identical production chain (extraction -> ... -> real packaging -> persisted
artifact) plus a fresh project-manager restart read-back, without importing Qt.

Provider = 0, network = 0, real translation = 0.
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

_TITLE = "S11-10 TOC Fallback Book"
_AUTHOR = "S11-10 Author"
_LANGUAGE = "en"
_IDENTIFIER = "urn:uuid:s11-10-fixture"

# Manifest declaration order deliberately differs from spine order.
MANIFEST_ORDER = ["item2", "item0", "item4", "item1", "item3", "img"]
SPINE = [
    ("item0", "yes"),
    ("item1", "no"),
    ("item2", "yes"),
    ("item3", "no"),
    ("item4", "yes"),
]

EXPECTED_POSITIONS = [1, 2, 3, 4, 5]
EXPECTED_IDS = ["ch0001", "ch0002", "ch0003", "ch0004", "ch0005"]
EXPECTED_TITLES = [
    "First From Nav",     # item0: nav fallback (Case A)
    "NCX Label One",      # item1: NCX fallback (Case C)
    "Document H1 Two",    # item2: document h1 outranks "Different TOC Label" (Case B)
    "Chapter 4",          # item3: generated fallback (Case D)
    "Chapter 5",          # item4: whitespace nav label rejected -> generated
]
EXPECTED_IS_LINEAR = [True, False, True, False, True]
EXPECTED_FINAL_LINEAR = [None, "no", None, "no", None]
EXPECTED_HREFS = ["item0.xhtml", "item1.xhtml", "item2.xhtml", "item3.xhtml", "item4.xhtml"]
# Final navigation is rebuilt from chapters in spine order; href->label mapping is
# the correctness property, not source-TOC order preservation.
EXPECTED_NAV = [
    ("item0.xhtml", "First From Nav"),
    ("item1.xhtml", "NCX Label One"),
    ("item2.xhtml", "Document H1 Two"),
    ("item3.xhtml", "Chapter 4"),
    ("item4.xhtml", "Chapter 5"),
]

_NS_XHTML = {"xhtml": "http://www.w3.org/1999/xhtml"}


# ---------------------------------------------------------------------------
# Deterministic fixture
# ---------------------------------------------------------------------------

def make_toc_book(tmp_path: Path, name: str = "toc_book.epub") -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    epub_path = tmp_path / name
    manifest_items = "".join(
        f'    <item id="{iid}" href="{iid}.xhtml" media-type="application/xhtml+xml"/>'
        for iid in MANIFEST_ORDER
        if iid != "img"
    )
    manifest_items += '\n    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
    manifest_items += '\n    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    manifest_items += '\n    <item id="img" href="img.png" media-type="image/png"/>'
    spine_items = "".join(
        f'    <itemref idref="{iid}" linear="{linear}"/>' for iid, linear in SPINE
    )
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
{manifest_items}
  </manifest>
  <spine toc="ncx">
{spine_items}
  </spine>
</package>""",
        )
        # Source nav order differs from spine order; item2 label is deliberately
        # different from its document h1, item4 label is whitespace-only.
        zf.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body>
    <nav epub:type="toc">
      <h2>Contents</h2>
      <ol>
        <li><a href="item2.xhtml">Different TOC Label</a></li>
        <li><a href="item0.xhtml">First From Nav</a></li>
        <li><a href="item4.xhtml">   </a></li>
      </ol>
    </nav>
  </body>
</html>""",
        )
        # NCX provides the only label for item1 (nav has no item1 entry).
        zf.writestr(
            "OEBPS/toc.ncx",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="{_IDENTIFIER}"/></head>
  <docTitle><text>{_TITLE}</text></docTitle>
  <navMap>
    <navPoint id="n1" playOrder="1">
      <navLabel><text>NCX Label One</text></navLabel>
      <content src="item1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>""",
        )
        for iid, _linear in SPINE:
            image = '<img src="img.png" alt="figure"/>' if iid == "item0" else ""
            h1 = "<h1>Document H1 Two</h1>" if iid == "item2" else ""
            body = (
                f"This chapter item is identified by the unique marker "
                f"CHAPTER_ITEM_{iid.replace('item', '')} and continues with several "
                f"ordinary English words of prose."
            )
            zf.writestr(
                f"OEBPS/{iid}.xhtml",
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">'
                "<head></head>"
                f"<body>{h1}<p>{body}</p>{image}</body></html>",
            )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\ns11-10")
    return epub_path


# ---------------------------------------------------------------------------
# Real-path helpers (no ordering-critical mocking)
# ---------------------------------------------------------------------------

def extract_and_intake(epub_path: Path):
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


def build_translation_input(epub_path: Path, result, intake) -> EpubTranslationInput:
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
        chapter_map=chapter_map,
        resources=resources,
        toc_entries=(),
        fixed_layout_info=None,
    )


def deterministic_epub_runtime(options) -> EpubTranslationResult:
    """Deterministic, chapter-aware, packaging-compatible fake runtime."""
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
        session_id="s11-10-deterministic",
        resume_state_path=None,
    )


def read_final_epub(path: Path) -> dict:
    """Fresh reopen + parse the persisted EPUB.

    Returns raw spine, per-chapter ``[ZH:chNNNN]`` identity markers, the production
    ``nav.xhtml`` labels/hrefs, and the archive name list.
    """
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        by_base = {Path(n).name: n for n in names}

        opf_name = next(n for n in names if n.endswith(".opf"))
        root = ET.fromstring(zf.read(opf_name))
        opf_ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {
            it.get("id"): it.get("href")
            for it in root.findall(".//opf:manifest/opf:item", opf_ns)
        }
        raw_spine = [
            (ir.get("idref"), ir.get("linear"), manifest.get(ir.get("idref")))
            for ir in root.findall(".//opf:spine/opf:itemref", opf_ns)
        ]

        chapter_entries = []
        for idref, linear, href in raw_spine:
            if not href or not href.endswith(".xhtml"):
                continue
            base = Path(href).name
            if idref == "nav" or base == "nav.xhtml":
                continue
            content = zf.read(by_base[base]).decode("utf-8")
            match = re.search(r"\[ZH:(ch\d{4})\]", content)
            chapter_entries.append((base, linear, match.group(1) if match else None))

        nav_name = by_base.get("nav.xhtml")
        nav_links: list[tuple[str, str]] = []
        if nav_name:
            nav_root = ET.fromstring(zf.read(nav_name))
            for a in nav_root.findall(".//xhtml:nav//xhtml:a", _NS_XHTML):
                nav_links.append((a.get("href", ""), "".join(a.itertext()).strip()))

        return {
            "names": names,
            "raw_spine": raw_spine,
            "chapter_entries": chapter_entries,
            "nav_links": nav_links,
        }


def run_pipeline(source: Path, output: Path) -> Path:
    result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    translation_result = deterministic_epub_runtime(
        type("O", (), {"chunks": chunks, "translation_input": ti})()
    )
    reader = build_epub_reader_chapter_map_with_metadata(
        translation_result=translation_result, translation_input=ti
    )
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
    assert output.is_file()
    return output


def run_direct_pipeline(tmp_path: Path) -> Path:
    source = make_toc_book(tmp_path)
    return run_pipeline(source, tmp_path / "out" / "toc_book_zh.epub")


def _spine_chapters(raw_spine):
    return [
        (idref, linear, href)
        for idref, linear, href in raw_spine
        if href and href.endswith(".xhtml") and Path(href).name != "nav.xhtml"
    ]


# ===========================================================================
# Test 1 — source -> extraction: title cases A/B/C/D + whitespace rejection
# ===========================================================================

def test_s11_10_extraction_title_cases_and_separation(tmp_path: Path) -> None:
    source = make_toc_book(tmp_path)
    result = EpubExtractionBoundary().extract(source)

    assert [c.spine_position for c in result.chapter_map] == EXPECTED_POSITIONS
    assert [c.title for c in result.chapter_map] == EXPECTED_TITLES
    assert [c.is_linear for c in result.chapter_map] == EXPECTED_IS_LINEAR
    assert [c.source_href for c in result.chapter_map] == [
        "OEBPS/item0.xhtml", "OEBPS/item1.xhtml", "OEBPS/item2.xhtml",
        "OEBPS/item3.xhtml", "OEBPS/item4.xhtml",
    ]
    # nav parsed (3 nav entries) + NCX (1 entry) proves R1/R2/NCX path are live
    assert result.extraction_manifest.nav_toc_entries >= 4
    # Case D / whitespace case are deterministic non-empty generated titles
    assert result.chapter_map[3].title == "Chapter 4"
    assert result.chapter_map[4].title == "Chapter 5"
    for c in result.chapter_map:
        assert c.title and c.title.strip()


# ===========================================================================
# Test 2 — intake -> EpubTranslationInput -> chunking preserves title/identity
# ===========================================================================

def test_s11_10_intake_and_chunking_preserve_title_identity_order(tmp_path: Path) -> None:
    source = make_toc_book(tmp_path)
    result, intake = extract_and_intake(source)
    assert intake.submission_eligible
    assert [c.title for c in (intake.chapter_map or ())] == EXPECTED_TITLES

    ti = build_translation_input(source, result, intake)
    assert [c.title for c in ti.chapter_map] == EXPECTED_TITLES
    assert [c.chapter_id for c in ti.chapter_map] == EXPECTED_IDS
    assert [c.spine_position for c in ti.chapter_map] == EXPECTED_POSITIONS
    assert [c.is_linear for c in ti.chapter_map] == EXPECTED_IS_LINEAR

    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    first_order = list(dict.fromkeys(c.chapter_id for c in chunks))
    assert first_order == EXPECTED_IDS
    for cid in EXPECTED_IDS:
        seqs = [c.chunk_sequence for c in chunks if c.chapter_id == cid]
        assert seqs == list(range(len(seqs)))


# ===========================================================================
# Test 3 — final persisted EPUB, fresh nav.xhtml read-back (primary proof)
# ===========================================================================

def test_s11_10_final_epub_fresh_nav_readback(tmp_path: Path) -> None:
    output = run_direct_pipeline(tmp_path)
    data = read_final_epub(output)

    # Primary proof: production-generated nav.xhtml labels + hrefs.
    assert data["nav_links"] == EXPECTED_NAV

    # href -> chapter identity marker (correct chapter, not merely a label).
    entries = data["chapter_entries"]
    assert [base for base, _linear, _marker in entries] == EXPECTED_HREFS
    assert [marker for _base, _linear, marker in entries] == EXPECTED_IDS

    spine_chapters = _spine_chapters(data["raw_spine"])
    # Spine ordering (S11-03/S11-04 lock).
    assert [href for _idref, _linear, href in spine_chapters] == EXPECTED_HREFS
    # Non-linear semantics (S11-06/S11-07 lock; None != "no").
    assert [linear for _idref, linear, _href in spine_chapters] == EXPECTED_FINAL_LINEAR

    # Resource mapping.
    assert any(Path(n).name == "img.png" for n in data["names"])


# ===========================================================================
# Test 4 — project-owned persistence + fresh manager restart read-back
# ===========================================================================

def test_s11_10_persistence_and_fresh_project_restart(tmp_path: Path) -> None:
    from core.reader_project.manager import ReaderProjectManager
    from core.reader_project.models import OutputRecord

    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    source = make_toc_book(tmp_path)
    project = manager.create(source, format="epub", title=_TITLE)

    output = run_pipeline(source, tmp_path / "out" / "toc_book_zh.epub")
    manager.update(
        project,
        output=OutputRecord(
            output_dir=str(output.parent),
            artifact_path=str(output),
            artifact_kind="epub",
            available=True,
        ),
    )

    # Fresh manager == restart; reopen the persisted project and its artifact.
    manager2 = ReaderProjectManager(home=home)
    reloaded = manager2.load(project.project_id)
    assert reloaded.output.artifact_kind == "epub"
    assert reloaded.output.available is True
    assert reloaded.output.artifact_path
    artifact = Path(reloaded.output.artifact_path)
    assert artifact.is_file()

    reread = read_final_epub(artifact)
    assert reread["nav_links"] == EXPECTED_NAV
    assert [marker for _b, _l, marker in reread["chapter_entries"]] == EXPECTED_IDS
    assert [linear for _i, linear, _h in _spine_chapters(reread["raw_spine"])] == EXPECTED_FINAL_LINEAR


# ===========================================================================
# Test 5 — deterministic repeat
# ===========================================================================

def test_s11_10_determinism_repeated_run(tmp_path: Path) -> None:
    first = read_final_epub(run_direct_pipeline(tmp_path / "run1"))
    second = read_final_epub(run_direct_pipeline(tmp_path / "run2"))

    assert first["nav_links"] == second["nav_links"] == EXPECTED_NAV
    assert first["chapter_entries"] == second["chapter_entries"]
    assert [l for _b, l, _m in first["chapter_entries"]] == EXPECTED_FINAL_LINEAR


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
