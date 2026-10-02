"""S10-03 — EPUB Reader-First Production E2E.

Real production path (extraction, intake, EpubTranslationInput, chunking,
packaging, Project persistence, output path) with a deterministic injected
runtime execution seam and fake OS opener. Provider = 0, network = 0,
real translation = 0.

No production extraction/intake/chunking/packaging/Project/output-path is
mocked. Only the runtime *execution* and the OS opener are injected.
"""

from __future__ import annotations

import time
import zipfile
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

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
from core.reader_project.models import ReaderStatus
from ui.translation_studio.project_view_model import build_card_model

_RUNTIME = "core.epub_translation.runtime.adapter.translate_epub_translation_input"
_MSGBOX = "ui.translation_studio.pages.project_page.QMessageBox"

_TITLE = "S10-03 Reader Book"
_AUTHOR = "S10-03 Author"
_LANGUAGE = "en"
_IDENTIFIER = "urn:uuid:s10-03-fixture"


# ---------------------------------------------------------------------------
# Deterministic EPUB fixture (2 chapters + referenced resource + nav)
# ---------------------------------------------------------------------------

def make_book_epub(
    tmp_path: Path,
    name: str = "reader_book.epub",
    title: str = _TITLE,
    identifier: str = _IDENTIFIER,
) -> Path:
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
    <dc:title>{title}</dc:title>
    <dc:creator>{_AUTHOR}</dc:creator>
    <dc:language>{_LANGUAGE}</dc:language>
    <dc:identifier id="bookid">{identifier}</dc:identifier>
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
<body><h1>Chapter One</h1><p>First chapter first paragraph.</p>
<p>First chapter second paragraph.</p><img src="img.png" alt="figure"/></body></html>""",
        )
        zf.writestr(
            "OEBPS/ch2.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter Two</title></head>
<body><h1>Chapter Two</h1><p>Second chapter content.</p></body></html>""",
        )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\ns10-03")
    return epub_path


# ---------------------------------------------------------------------------
# Real path helpers (no mocking)
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
        chapter_map=chapter_map, resources=resources, toc_entries=(), fixed_layout_info=None,
    )


def deterministic_epub_runtime(options, root=None, engine=None) -> EpubTranslationResult:
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
        session_id="s10-03-deterministic",
        resume_state_path=None,
    )


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


def read_epub(epub_path: Path) -> dict:
    with zipfile.ZipFile(epub_path) as zf:
        names = zf.namelist()
        opf_name = next(n for n in names if n.endswith(".opf"))
        data = {"names": names, "opf": zf.read(opf_name).decode("utf-8"), "xhtml": {}}
        for n in names:
            if n.endswith(".xhtml"):
                data["xhtml"][Path(n).name] = zf.read(n).decode("utf-8")
    return data


def _has_name(names: list[str], basename: str) -> bool:
    return any(Path(n).name == basename for n in names)


# ===========================================================================
# E2E-02..E2E-05, E2E-09..E2E-12 — real production path (no UI)
# ===========================================================================

def test_e2e_real_extraction_offsets_identity(tmp_path):
    source = make_book_epub(tmp_path)
    result = EpubExtractionBoundary().extract(source)
    assert result.status == "success"
    assert len(result.chapter_map) == 2

    for ch in result.chapter_map:
        marker = f"=== CHAPTER {ch.index}: {ch.title} ===\n"
        body_start = ch.body_start_offset
        body_end = ch.body_end_offset
        assert body_start is not None and body_end is not None
        assert result.extracted_text[ch.start_offset:ch.start_offset + len(marker)] == marker
        assert body_start == ch.start_offset + len(marker)
        assert body_end == ch.end_offset - 1
        body = result.extracted_text[body_start:body_end]
        assert body.strip() and "===" not in body

    c1, c2 = result.chapter_map
    assert c1.spine_position == 1 and c2.spine_position == 2
    assert c1.body_end_offset is not None and c2.body_start_offset is not None
    assert c1.body_end_offset <= c2.body_start_offset


def test_e2e_real_intake_preserves_metadata_and_resource(tmp_path):
    source = make_book_epub(tmp_path)
    result, intake = extract_and_intake(source)
    assert intake.submission_eligible
    metadata = intake.epub_metadata
    assert metadata is not None
    assert metadata["title"] == _TITLE
    assert metadata["author"] == _AUTHOR
    assert metadata["language"] == _LANGUAGE
    assert metadata["identifier"] == _IDENTIFIER
    assert metadata["raw"]
    assert intake.resource_refs and any(r.type == "image" for r in intake.resource_refs)
    ti = build_translation_input(source, result, intake)
    assert ti.original_hash == result.original_hash
    assert len(ti.chapter_map) == 2


def test_e2e_identifier_yields_filesystem_safe_output_dir(tmp_path):
    from core.epub_translation.output_layout import epub_output_dir, safe_output_segment

    segment = safe_output_segment(_IDENTIFIER)
    assert ":" not in segment and segment
    out_dir = epub_output_dir(tmp_path, _IDENTIFIER)
    out_dir.mkdir(parents=True, exist_ok=True)  # would raise WinError 123 if unsanitized
    assert out_dir.is_dir()


def test_e2e_real_chunking(tmp_path):
    source = make_book_epub(tmp_path)
    result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    assert chunks
    chapter_ids = {c.chapter_id for c in ti.chapter_map}
    assert {c.chapter_id for c in chunks} == chapter_ids
    for chunk in chunks:
        assert chunk.source_text and "===" not in chunk.source_text
        assert chunk.extracted_start_offset >= 0


def test_e2e_real_packaging_produces_final_epub(tmp_path):
    source = make_book_epub(tmp_path)
    result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    translation_result = deterministic_epub_runtime(type("O", (), {"chunks": chunks, "translation_input": ti})())
    reader = build_epub_reader_chapter_map_with_metadata(
        translation_result=translation_result, translation_input=ti
    )
    output = tmp_path / "out" / "reader_book_zh.epub"
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

    data = read_epub(output)
    # chapter order / count
    assert _has_name(data["names"], "ch1.xhtml")
    assert _has_name(data["names"], "ch2.xhtml")
    # translated bodies mapped to correct chapters
    assert "[ZH:ch0001]" in data["xhtml"]["ch1.xhtml"]
    assert "[ZH:ch0002]" in data["xhtml"]["ch2.xhtml"]
    assert "[ZH:ch0002]" not in data["xhtml"]["ch1.xhtml"]
    # metadata integrity in final OPF
    assert _TITLE in data["opf"] and _AUTHOR in data["opf"]
    # resource integrity
    assert _has_name(data["names"], "img.png")
    # navigable
    assert _has_name(data["names"], "nav.xhtml")


# ===========================================================================
# E2E-06..E2E-15, E2E-27 — full reader journey through the real UI entry
# ===========================================================================

def test_e2e_full_reader_journey(qapp, tmp_path, manager, opener, page):
    source = make_book_epub(tmp_path)

    # Import + real extraction + preview content (canonical extraction output)
    result = EpubExtractionBoundary().extract(source)
    info = book_info(source, result)
    assert info["preview_text"].strip()
    assert len(info["chapter_map"]) == 2

    # Project persistence (real)
    pid = page.add_project(name=info["title"], source=str(source), book_info=info)
    assert pid is not None
    page.table.selectRow(0)
    stored = manager.load(pid)
    assert stored.source.format == "epub"
    assert stored.source.identity_kind == "epub_sha256"
    assert len(stored.source.hash) == 64

    # Translation entry through the real UI route with a real runner and an
    # injected deterministic runtime execution.
    with patch(_RUNTIME, deterministic_epub_runtime), patch(_MSGBOX):
        page._on_translate()
        assert wait_complete(qapp, page), "translation did not complete"

    stored = manager.load(pid)
    artifact = stored.output.artifact_path
    assert artifact and Path(artifact).is_file()
    assert stored.output.artifact_kind == "epub"
    assert stored.output.available is True
    assert Path(artifact).name.endswith("_zh.epub")

    # Deterministic chapter content present in the packaged artifact
    data = read_epub(Path(artifact))
    assert "[ZH:ch0001]" in data["xhtml"]["ch1.xhtml"]
    assert "[ZH:ch0002]" in data["xhtml"]["ch2.xhtml"]
    assert _TITLE in data["opf"]

    # Completed reader status + record derived from persisted facts
    model = build_card_model(manager.load(pid))
    assert model.reader_status == ReaderStatus.COMPLETED.value
    assert model.can_open_result is True

    # Open Result uses the persisted artifact path (fake OS opener)
    page._on_open_result(pid)
    assert opener.opened and opener.opened[-1] == artifact

    # Restart / restore
    from core.reader_project.manager import ReaderProjectManager
    from ui.translation_studio.pages.project_page import ProjectPage
    page2 = ProjectPage()
    page2.set_project_manager(ReaderProjectManager(home=manager.store.home))
    page2.set_result_opener(opener)
    page2.refresh_projects()
    assert pid is not None
    try:
        assert pid in page2._persisted_ids
        reloaded = manager.load(pid)
        assert reloaded.output.artifact_path == artifact
        assert reloaded.output.artifact_kind == "epub"
        assert build_card_model(reloaded).can_open_result is True
        page2._on_open_result(str(pid))
        assert opener.opened[-1] == artifact
    finally:
        page2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
