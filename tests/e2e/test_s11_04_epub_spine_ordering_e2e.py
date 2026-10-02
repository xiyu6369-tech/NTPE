"""S11-04 — EPUB Spine Ordering Reader-First E2E Verification.

Verifies the S11-03 repair along the real production path:

  source EPUB (interspersed linear="no")
    -> extraction boundary
    -> canonical intake
    -> EpubTranslationInput
    -> chunking
    -> production translation entry (deterministic injected runtime execution)
    -> real EPUB packaging
    -> persisted final EPUB
    -> fresh read-back (reopen + parse)

Ordering-critical layers are NOT mocked: extraction, intake, input construction,
chunking, packaging and final-EPUB parsing are the real production code. Only the
runtime *execution* (provider/model/network) and the OS opener are injected.

Provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import re
import time
import zipfile
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch
from xml.etree import ElementTree as ET

import pytest

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

_RUNTIME = "core.epub_translation.runtime.adapter.translate_epub_translation_input"
_MSGBOX = "ui.translation_studio.pages.project_page.QMessageBox"

_TITLE = "S11-04 Ordering Book"
_AUTHOR = "S11-04 Author"
_LANGUAGE = "en"
_IDENTIFIER = "urn:uuid:s11-04-fixture"

# Manifest declaration order deliberately differs from spine order.
MANIFEST_ORDER = ["item2", "item0", "item4", "item1", "item3"]
# Canonical spine: linear / non-linear / linear / non-linear / linear.
SPINE = [
    ("item0", "yes"),
    ("item1", "no"),
    ("item2", "yes"),
    ("item3", "no"),
    ("item4", "yes"),
]
EXPECTED_TITLES = ["item0", "item1", "item2", "item3", "item4"]
EXPECTED_POSITIONS = [1, 2, 3, 4, 5]
EXPECTED_IDS = ["ch0001", "ch0002", "ch0003", "ch0004", "ch0005"]
EXPECTED_IS_LINEAR = [True, False, True, False, True]
EXPECTED_BASENAMES = ["item0.xhtml", "item1.xhtml", "item2.xhtml", "item3.xhtml", "item4.xhtml"]
# Pre-repair defect shape: partition-then-concat ordering.
DEFECT_POSITIONS = [1, 3, 5, 2, 4]


# ---------------------------------------------------------------------------
# Deterministic EPUB fixture
# ---------------------------------------------------------------------------

def make_interspersed_epub(tmp_path: Path, name: str = "ordering_book.epub") -> Path:
    epub_path = tmp_path / name
    manifest_items = "".join(
        f'    <item id="{iid}" href="{iid}.xhtml" media-type="application/xhtml+xml"/>'
        for iid in MANIFEST_ORDER
    )
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
  <spine>
{spine_items}
  </spine>
</package>""",
        )
        for iid, _linear in SPINE:
            image = '<img src="img.png" alt="figure"/>' if iid == "item0" else ""
            # Sufficient English prose keeps deterministic intake eligible; the
            # unique marker CHAPTER_ITEMn identifies the chapter in the final EPUB.
            body = (
                f"This chapter item is identified by the unique marker "
                f"CHAPTER_{iid.upper()} and continues with several ordinary English "
                f"words of prose so that deterministic intake remains eligible."
            )
            zf.writestr(
                f"OEBPS/{iid}.xhtml",
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">'
                f"<head><title>{iid}</title></head>"
                f"<body><h1>{iid}</h1><p>{body}</p>{image}</body></html>",
            )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\ns11-04")
    return epub_path


# ---------------------------------------------------------------------------
# Real-path helpers (ordering-critical layers are NOT mocked)
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


def deterministic_epub_runtime(options, root=None, engine=None) -> EpubTranslationResult:
    """Deterministic chapter-aware runtime; preserves chapter identity/order.

    Output text carries the source chapter identity as ``[ZH:chNNNN]`` so the
    packaged EPUB can be re-read and proven to map each spine item to the correct
    source chapter.
    """
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
        session_id="s11-04-deterministic",
        resume_state_path=None,
    )


def run_direct_pipeline(tmp_path: Path) -> Path:
    """Real extraction -> intake -> input -> chunking -> injected runtime -> packaging."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = make_interspersed_epub(tmp_path)
    result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    translation_result = deterministic_epub_runtime(
        type("O", (), {"chunks": chunks, "translation_input": ti})()
    )
    reader = build_epub_reader_chapter_map_with_metadata(
        translation_result=translation_result, translation_input=ti
    )
    output = tmp_path / "out" / "ordering_book_zh.epub"
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


def read_final_epub(path: Path) -> dict:
    """Freshly reopen and parse a packaged EPUB (no in-memory reuse)."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        by_base = {Path(n).name: n for n in names}
        opf_name = next(n for n in names if n.endswith(".opf"))
        root = ET.fromstring(zf.read(opf_name))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {it.get("id"): it.get("href") for it in root.findall(".//opf:manifest/opf:item", ns)}
        spine = [
            (ir.get("idref"), ir.get("linear"))
            for ir in root.findall(".//opf:spine/opf:itemref", ns)
        ]
        chapter_hrefs: list[str] = []
        chapter_markers: dict[str, str | None] = {}
        for idref, _linear in spine:
            href = manifest.get(idref)
            if not href or not href.endswith(".xhtml"):
                continue
            base = Path(href).name
            if idref == "nav" or base == "nav.xhtml":
                continue  # navigation document is not a chapter item
            content = zf.read(by_base[base]).decode("utf-8")
            match = re.search(r"\[ZH:(ch\d{4})\]", content)
            chapter_markers[base] = match.group(1) if match else None
            chapter_hrefs.append(base)
        return {
            "names": names,
            "manifest": manifest,
            "spine": spine,
            "chapter_hrefs": chapter_hrefs,
            "chapter_markers": chapter_markers,
        }


def book_info(source: Path, result) -> dict:
    metadata = result.metadata
    return {
        "title": metadata.title or source.stem,
        "source": str(source),
        "format": "epub",
        "chapters": len(result.chapter_map),
        "chars": len(result.extracted_text),
        "status": result.status,
        "warnings": list(result.warnings),
        "preview_text": result.extracted_text,
        "metadata": {
            "title": metadata.title, "author": metadata.author,
            "language": metadata.language, "identifier": metadata.identifier,
        },
        "chapter_map": [
            {"index": c.index, "title": c.title, "start_offset": c.start_offset,
             "end_offset": c.end_offset, "word_count": c.word_count, "is_linear": c.is_linear}
            for c in result.chapter_map
        ],
    }


def wait_complete(qapp, page, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        qapp.processEvents()
        if page._translation_runner is None:
            return True
        time.sleep(0.02)
    return False


# ===========================================================================
# Q1 — extraction
# ===========================================================================

def test_s11_04_extraction_preserves_interspersed_canonical_order(tmp_path: Path) -> None:
    source = make_interspersed_epub(tmp_path)
    result = EpubExtractionBoundary().extract(source)
    cm = result.chapter_map

    assert result.status == "success"
    assert [c.spine_position for c in cm] == EXPECTED_POSITIONS
    assert [c.spine_position for c in cm] != DEFECT_POSITIONS  # lock S11-03 defect shape
    assert [c.index for c in cm] == EXPECTED_POSITIONS
    assert [c.title for c in cm] == EXPECTED_TITLES
    assert [c.is_linear for c in cm] == EXPECTED_IS_LINEAR
    assert len(cm) == 5  # supplementary retained, not dropped
    assert [c.status for c in cm] == ["linear", "supplementary", "linear", "supplementary", "linear"]

    # Extraction text is emitted in canonical spine order.
    marker_titles = re.findall(r"=== CHAPTER \d+: (.+?) ===", result.extracted_text)
    assert marker_titles == EXPECTED_TITLES


# ===========================================================================
# Q2 — intake / input / chunking
# ===========================================================================

def test_s11_04_intake_input_chunking_preserve_order_and_identity(tmp_path: Path) -> None:
    source = make_interspersed_epub(tmp_path)
    result, intake = extract_and_intake(source)
    assert intake.submission_eligible
    assert [c.spine_position for c in (intake.chapter_map or ())] == EXPECTED_POSITIONS

    ti = build_translation_input(source, result, intake)
    assert [c.chapter_id for c in ti.chapter_map] == EXPECTED_IDS
    assert [c.spine_position for c in ti.chapter_map] == EXPECTED_POSITIONS
    assert [c.is_linear for c in ti.chapter_map] == EXPECTED_IS_LINEAR
    assert [c.title for c in ti.chapter_map] == EXPECTED_TITLES

    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    assert chunks
    # First-occurrence chapter order equals canonical spine order (no test-side sort).
    first_order = list(dict.fromkeys(c.chapter_id for c in chunks))
    assert first_order == EXPECTED_IDS
    # Per-chapter chunk sequence starts at 0 and is contiguous.
    for cid in EXPECTED_IDS:
        seqs = [c.chunk_sequence for c in chunks if c.chapter_id == cid]
        assert seqs == list(range(len(seqs)))


# ===========================================================================
# Q3 + Q4 — packaging, final EPUB read-back, resource mapping
# ===========================================================================

def test_s11_04_final_epub_spine_order_and_resource_mapping(tmp_path: Path) -> None:
    output = run_direct_pipeline(tmp_path)
    data = read_final_epub(output)

    # Final EPUB spine (chapter items, excluding nav) preserves canonical order.
    assert data["chapter_hrefs"] == EXPECTED_BASENAMES

    # Each spine item maps to the correct source chapter content marker.
    assert data["chapter_markers"] == {
        "item0.xhtml": "ch0001",
        "item1.xhtml": "ch0002",
        "item2.xhtml": "ch0003",
        "item3.xhtml": "ch0004",
        "item4.xhtml": "ch0005",
    }

    # Supplementary items stay at positions 2 and 4; not moved to the end.
    assert data["chapter_hrefs"][1] == "item1.xhtml"
    assert data["chapter_hrefs"][3] == "item3.xhtml"

    # Resource mapping: referenced image preserved and reachable by basename.
    assert any(Path(n).name == "img.png" for n in data["names"])


def test_s11_04_final_epub_linear_attribute_observation(tmp_path: Path) -> None:
    """Records current packaging behaviour for the ``linear`` attribute.

    S11-04 ordering scope: the final spine ORDER is canonical (verified above).
    This test documents that the packager does not currently emit ``linear="no"``
    in the output EPUB (all spine itemrefs default to linear). This is recorded as
    an independent finding (DEF-1) in the S11-04 report and is NOT fixed here.
    """
    output = run_direct_pipeline(tmp_path)
    data = read_final_epub(output)
    linear_attrs = [linear for _idref, linear in data["spine"]]
    assert all(linear is None for linear in linear_attrs), linear_attrs


# ===========================================================================
# Reader-first UI journey (production entry + persistence + restart)
# ===========================================================================

def test_s11_04_reader_first_ui_journey_persists_ordered_epub(qapp, tmp_path, manager, opener, page):
    source = make_interspersed_epub(tmp_path)
    result = EpubExtractionBoundary().extract(source)
    info = book_info(source, result)
    assert info["preview_text"].strip()

    pid = page.add_project(name=info["title"], source=str(source), book_info=info)
    assert pid is not None
    page.table.selectRow(0)
    stored = manager.load(pid)
    assert stored.source.format == "epub"
    assert stored.source.identity_kind == "epub_sha256"

    # Real production entry with deterministic injected runtime execution.
    with patch(_RUNTIME, deterministic_epub_runtime), patch(_MSGBOX):
        page._on_translate()
        assert wait_complete(qapp, page), "translation did not complete"

    stored = manager.load(pid)
    artifact = stored.output.artifact_path
    assert artifact and Path(artifact).is_file()
    assert stored.output.artifact_kind == "epub"
    assert stored.output.available is True

    # Fresh read-back of the persisted artifact proves canonical order and identity.
    data = read_final_epub(Path(artifact))
    assert data["chapter_hrefs"] == EXPECTED_BASENAMES
    assert [data["chapter_markers"][b] for b in EXPECTED_BASENAMES] == EXPECTED_IDS

    # Lightweight restart: a new page reloads the same persisted ordered artifact.
    from core.reader_project.manager import ReaderProjectManager
    from ui.translation_studio.pages.project_page import ProjectPage

    page2 = ProjectPage()
    page2.set_project_manager(ReaderProjectManager(home=manager.store.home))
    page2.set_result_opener(opener)
    page2.refresh_projects()
    try:
        assert pid in page2._persisted_ids
        reloaded = manager.load(pid)
        assert reloaded.output.artifact_path == artifact
        assert read_final_epub(Path(reloaded.output.artifact_path))["chapter_hrefs"] == EXPECTED_BASENAMES
    finally:
        page2.close()


# ===========================================================================
# Determinism
# ===========================================================================

def test_s11_04_determinism_repeated_run_preserves_order_and_identity(tmp_path: Path) -> None:
    first = read_final_epub(run_direct_pipeline(tmp_path / "run1"))
    second = read_final_epub(run_direct_pipeline(tmp_path / "run2"))

    assert first["chapter_hrefs"] == second["chapter_hrefs"] == EXPECTED_BASENAMES
    assert first["chapter_markers"] == second["chapter_markers"]
    assert [m for m in (first["chapter_markers"][b] for b in EXPECTED_BASENAMES)] == EXPECTED_IDS
    # Spine structural signature (idref order + linear attrs) is stable.
    assert first["spine"] == second["spine"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
