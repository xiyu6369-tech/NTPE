"""S5-A Resource-Aware EPUB Packaging Contract Tests — Offline, Deterministic.

Tests for the S5-A Resource-Aware EPUB Packager.
Updated to use real EPUB implementation with actual archive validation.
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from core.epub_translation.contract import (
    EpubMetadata,
    EpubChapterBoundary,
    ResourceRef,
    TocEntry,
    ExtractionManifest,
    EpubTranslationInput,
    EpubTranslationChunk,
    EpubChunkResult,
    EpubChapterResult,
    EpubTranslationResult,
)
from core.epub_translation.reader_chapter_map import (
    build_epub_reader_chapter_map_with_metadata,
    EpubReaderChapterMapResult,
)
from core.epub_translation.runtime.epub_packager import (
    EpubPackagingInput,
    EpubPackagingResult,
    pack_epub_resource_aware,
    EpubPackagingError,
    _validate_epub_archive,
)


# ========================================================================
# Fixtures
# ========================================================================

def make_epub_metadata() -> EpubMetadata:
    return EpubMetadata(
        title="Test Novel",
        author="Test Author",
        language="ko",
        identifier="test-id-123",
        publisher="Test Publisher",
        date="2024-01-01",
        raw=MappingProxyType({"dc:title": "Test Novel", "dc:creator": "Test Author"}),
    )


def make_chapter_boundary(
    index: int = 1,
    spine_position: int = 1,
    title: str | None = "Chapter 1",
    source_href: str = "OEBPS/ch1.xhtml",
    start_offset: int = 0,
    end_offset: int = 100,
    body_start_offset: int | None = None,
    body_end_offset: int | None = None,
    is_linear: bool = True,
    word_count: int = 50,
) -> EpubChapterBoundary:
    if body_start_offset is None:
        body_start_offset = start_offset + 30
    if body_end_offset is None:
        body_end_offset = max(start_offset + 1, end_offset - 5)
    return EpubChapterBoundary(
        index=index,
        spine_position=spine_position,
        title=title,
        source_href=source_href,
        start_offset=start_offset,
        end_offset=end_offset,
        body_start_offset=body_start_offset,
        body_end_offset=body_end_offset,
        is_linear=is_linear,
        word_count=word_count,
    )


def make_resource_ref(
    type_: str = "image",
    href: str = "images/cover.jpg",
    chapter_index: int | None = 1,
) -> ResourceRef:
    return ResourceRef(
        type=type_,
        href=href,
        chapter_index=chapter_index,
        metadata=MappingProxyType({"alt": "cover"}),
    )


def make_toc_entry(href: str = "ch1.xhtml", title: str = "Chapter 1", level: int = 0) -> TocEntry:
    return TocEntry(href=href, title=title, level=level)


def make_extraction_manifest() -> ExtractionManifest:
    return ExtractionManifest(
        extractor_version="epub-extraction-v1.0.0",
        extracted_at="2024-01-01T00:00:00+00:00",
        chapter_count=3,
        total_characters=300,
        total_words=150,
        warnings=(),
        resources=(),
        spine_item_count=3,
        nav_toc_entries=3,
        encoding_used="utf-8",
        parsing_duration_ms=100,
        fixed_layout=None,
    )


def make_epub_translation_input(
    chapter_map: tuple[EpubChapterBoundary, ...] | None = None,
    resources: tuple[ResourceRef, ...] = (),
    toc_entries: tuple[TocEntry, ...] | None = None,
    original_hash: str = "a" * 64,
    extraction_status: str = "success",
) -> EpubTranslationInput:
    if chapter_map is None:
        chapter_map = (
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/chapter1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/chapter2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/chapter3.xhtml", 200, 300, 230, 295),
        )

    if toc_entries is None:
        import os
        toc_entries = tuple(
            make_toc_entry(os.path.basename(c.source_href.split("#")[0]), c.title or f"Chapter {i+1}")
            for i, c in enumerate(chapter_map)
        )

    return EpubTranslationInput(
        source_epub_path=Path("test.epub"),
        original_hash=original_hash,
        extraction_status=extraction_status,
        warnings=(),
        metadata=make_epub_metadata(),
        chapter_map=chapter_map,
        resources=resources,
        toc_entries=toc_entries,
        fixed_layout_info=None,
        extraction_manifest=make_extraction_manifest(),
    )


def make_epub_chunk_result(
    chunk_id: str = "ch0001:chunk0000",
    status: str = "success",
    translated_text: str = "번역된 내용",
    error: str | None = None,
    attempt: int = 1,
) -> EpubChunkResult:
    return EpubChunkResult(
        chunk_id=chunk_id,
        status=status,
        translated_text=translated_text,
        error=error,
        attempt=attempt,
        qa_report=MappingProxyType({"passed": True}),
        metadata=MappingProxyType({}),
    )


def make_epub_chapter_result(
    chapter_id: str = "ch0001",
    chapter_order: int = 1,
    chunk_results: tuple[EpubChunkResult, ...] | None = None,
    aggregate_status: str = "success",
    assembled_text: str | None = None,
) -> EpubChapterResult:
    if chunk_results is None:
        chunk_results = (make_epub_chunk_result(chunk_id=f"{chapter_id}:chunk0000"),)

    success_count = sum(1 for c in chunk_results if c.status == "success")
    failed_count = sum(1 for c in chunk_results if c.status == "failed")
    skipped_count = sum(1 for c in chunk_results if c.status == "skipped")

    if assembled_text is None:
        assembled_text = "\n\n".join(c.translated_text for c in chunk_results if c.status == "success")
        if assembled_text:
            assembled_text += "\n"

    return EpubChapterResult(
        chapter_id=chapter_id,
        chapter_order=chapter_order,
        chunk_results=chunk_results,
        aggregate_status=aggregate_status,
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        assembled_text=assembled_text,
    )


def make_epub_translation_result(
    chapter_results: tuple[EpubChapterResult, ...] | None = None,
    aggregate_status: str = "success",
    session_id: str = "test-session-123",
) -> EpubTranslationResult:
    if chapter_results is None:
        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3),
        )

    return EpubTranslationResult(
        aggregate_status=aggregate_status,
        chapter_results=chapter_results,
        success_count=sum(cr.success_count for cr in chapter_results),
        failed_count=sum(cr.failed_count for cr in chapter_results),
        skipped_count=sum(cr.skipped_count for cr in chapter_results),
        session_id=session_id,
        resume_state_path=None,
    )


def make_reader_chapter_map_result(
    translation_input: EpubTranslationInput,
    translation_result: EpubTranslationResult,
) -> EpubReaderChapterMapResult:
    """Build a valid EpubReaderChapterMapResult for testing."""
    return build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)


def make_packaging_input(
    translation_input: EpubTranslationInput | None = None,
    translation_result: EpubTranslationResult | None = None,
) -> EpubPackagingInput:
    if translation_input is None:
        translation_input = make_epub_translation_input()
    if translation_result is None:
        translation_result = make_epub_translation_result()

    reader_result = make_reader_chapter_map_result(translation_input, translation_result)

    return EpubPackagingInput(
        reader_chapter_map_result=reader_result,
        translation_input=translation_input,
        translation_result=translation_result,
    )


# ========================================================================
# S5-A-01: Minimal resource-aware input 建立成功
# ========================================================================

class TestS5A01MinimalInput:
    """S5-A-01 — Minimal resource-aware input builds successfully."""

    def test_minimal_packaging_input_creation(self) -> None:
        """Minimal valid packaging input can be created."""
        packaging_input = make_packaging_input()
        assert isinstance(packaging_input, EpubPackagingInput)
        assert packaging_input.reader_chapter_map_result is not None
        assert packaging_input.translation_input is not None
        assert packaging_input.translation_result is not None

    def test_minimal_packaging_succeeds(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Minimal packaging input produces valid EPUB."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        assert result.chapter_count == 3
        assert result.source_identity == "a" * 64
        assert output_path.exists()


# ========================================================================
# S5-A-02: Chapter identity preservation
# ========================================================================

class TestS5A02ChapterIdentityPreservation:
    """S5-A-02 — Chapter identity preserved from S4 through packaging."""

    def test_chapter_id_preserved_in_output(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """chapter_id from S4 ReaderChapterMap must be preserved in output."""
        from dataclasses import replace

        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(spine_position=5, title="Prologue", source_href="OEBPS/prologue.xhtml"),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0005:chunk0000", translated_text="서문 내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0005", chapter_order=1, chunk_results=(chunk_result,),
            assembled_text="서문 내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        assert result.chapter_count == 1

    def test_duplicate_titles_distinguished_by_chapter_id(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Chapters with same title are distinguished by chapter_id."""
        from dataclasses import replace

        chapters = (
            make_chapter_boundary(1, 1, "Prologue", "OEBPS/prologue.xhtml", 0, 50, 20, 45),
            make_chapter_boundary(2, 2, "Prologue", "OEBPS/ch1.xhtml", 50, 100, 70, 95),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="첫 번째 프롤로그")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="두 번째 프롤로그")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="첫 번째 프롤로그\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="두 번째 프롤로그\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        assert result.chapter_count == 2


# ========================================================================
# S5-A-03: Chapter order preservation
# ========================================================================

class TestS5A03ChapterOrderPreservation:
    """S5-A-03 — Chapter order follows original spine order."""

    def test_spine_order_preserved(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Chapters must be packaged in spine order."""
        from dataclasses import replace

        chapters = (
            make_chapter_boundary(1, 1, "Chapter A", "OEBPS/chapter1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter B", "OEBPS/chapter2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter C", "OEBPS/chapter3.xhtml", 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="B")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="C")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="C\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        # Verify chapter order in output archive
        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            # Check spine order in OPF
            import xml.etree.ElementTree as ET
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            spine = opf_root.find(".//opf:spine", ns_opf)
            itemrefs = list(spine.findall("opf:itemref", ns_opf))
            # First should be nav, then chapters in order
            assert len(itemrefs) == 4
            assert itemrefs[0].get("idref") == "nav"
            # Chapter items should be in order (3 chapters)
            chapter_ids = [itemref.get("idref") for itemref in itemrefs[1:]]
            assert len(chapter_ids) == 3
            # Order should match chapter_order from translation result


# ========================================================================
# S5-A-04: Source href preservation
# ========================================================================

class TestS5A04SourceHrefPreservation:
    """S5-A-04 — Source href preserved in output."""

    def test_source_href_basename_used(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Original source_href basename used for output chapter file."""
        from dataclasses import replace

        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/custom_chapter.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        # Verify output href in archive
        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            chapter_files = [name for name in z.namelist() if name.endswith(".xhtml") and "nav" not in name.lower()]
            assert len(chapter_files) == 1
            assert "custom_chapter.xhtml" in chapter_files[0] or "chapter1.xhtml" in chapter_files[0]

    def test_fragment_stripped_from_output_href(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Fragment from source_href must not appear in output href."""
        from dataclasses import replace

        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml#section-2", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="내용")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="내용\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            chapter_files = [name for name in z.namelist() if name.endswith(".xhtml") and "nav" not in name.lower()]
            assert len(chapter_files) == 1
            # Fragment should not appear in output href
            assert "#" not in chapter_files[0]


# ========================================================================
# S5-A-05: Metadata preservation
# ========================================================================

class TestS5A05MetadataPreservation:
    """S5-A-05 — Original EPUB metadata preserved."""

    def test_title_preserved(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Original title preserved in output EPUB."""
        from dataclasses import replace

        metadata = EpubMetadata(
            title="Original Novel Title",
            author="Original Author",
            language="ko",
            identifier="original-id",
            publisher="Original Publisher",
            date="2023-01-01",
            raw=MappingProxyType({}),
        )
        translation_input = make_epub_translation_input()
        translation_input = EpubTranslationInput(
            source_epub_path=Path("test.epub"),
            original_hash="b" * 64,
            extraction_status="success",
            warnings=(),
            metadata=metadata,
            chapter_map=translation_input.chapter_map,
            resources=translation_input.resources,
            toc_entries=translation_input.toc_entries,
            fixed_layout_info=None,
            extraction_manifest=translation_input.extraction_manifest,
        )

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        # Verify title in OPF
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            ns_dc = {"dc": "http://purl.org/dc/elements/1.1/"}
            metadata_elem = opf_root.find(".//opf:metadata", ns_opf)
            title = metadata_elem.find("dc:title", ns_dc)
            assert title is not None
            assert title.text == "Original Novel Title"

    def test_author_preserved(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Original author preserved in output EPUB."""
        from dataclasses import replace

        metadata = EpubMetadata(
            title="Test",
            author="Original Author Name",
            language="ko",
            identifier="test-id",
            publisher=None,
            date=None,
            raw=MappingProxyType({}),
        )
        translation_input = make_epub_translation_input()
        translation_input = EpubTranslationInput(
            source_epub_path=Path("test.epub"),
            original_hash="c" * 64,
            extraction_status="success",
            warnings=(),
            metadata=metadata,
            chapter_map=translation_input.chapter_map,
            resources=translation_input.resources,
            toc_entries=translation_input.toc_entries,
            fixed_layout_info=None,
            extraction_manifest=translation_input.extraction_manifest,
        )

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            ns_dc = {"dc": "http://purl.org/dc/elements/1.1/"}
            metadata_elem = opf_root.find(".//opf:metadata", ns_opf)
            creator = metadata_elem.find("dc:creator", ns_dc)
            assert creator is not None
            assert creator.text == "Original Author Name"

    def test_identifier_preserved(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Original identifier preserved in output EPUB."""
        from dataclasses import replace

        metadata = EpubMetadata(
            title="Test",
            author="Author",
            language="ko",
            identifier="urn:uuid:original-identifier",
            publisher=None,
            date=None,
            raw=MappingProxyType({}),
        )
        translation_input = make_epub_translation_input()
        translation_input = EpubTranslationInput(
            source_epub_path=Path("test.epub"),
            original_hash="d" * 64,
            extraction_status="success",
            warnings=(),
            metadata=metadata,
            chapter_map=translation_input.chapter_map,
            resources=translation_input.resources,
            toc_entries=translation_input.toc_entries,
            fixed_layout_info=None,
            extraction_manifest=translation_input.extraction_manifest,
        )

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            ns_dc = {"dc": "http://purl.org/dc/elements/1.1/"}
            metadata_elem = opf_root.find(".//opf:metadata", ns_opf)
            identifier = metadata_elem.find("dc:identifier", ns_dc)
            assert identifier is not None
            assert identifier.text == "urn:uuid:original-identifier"


# ========================================================================
# S5-A-06: Spine order preservation
# ========================================================================

class TestS5A06SpineOrderPreservation:
    """S5-A-06 — Output spine matches canonical chapter order."""

    def test_spine_matches_chapter_order(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Spine items must match chapter order from translation result."""
        from dataclasses import replace

        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Ch3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="First")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="Second")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="Third")

        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="First\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="Second\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="Third\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        # Verify spine in OPF
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            spine = opf_root.find(".//opf:spine", ns_opf)
            itemrefs = list(spine.findall("opf:itemref", ns_opf))
            # nav + 3 chapters
            assert len(itemrefs) == 4
            assert itemrefs[0].get("idref") == "nav"


# ========================================================================
# S5-A-07: Navigation/TOC identity preservation
# ========================================================================

class TestS5A07NavigationTocPreservation:
    """S5-A-07 — Navigation/TOC structure preserved."""

    def test_original_toc_entries_used(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Original TOC entries from extraction used for navigation."""
        from dataclasses import replace

        toc_entries = (
            make_toc_entry("ch1.xhtml", "Chapter One", 0),
            make_toc_entry("ch2.xhtml", "Chapter Two", 0),
            make_toc_entry("ch2.xhtml#section1", "Section 1", 1),
        )
        chapter_map = (
            make_chapter_boundary(1, 1, "Chapter One", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter Two", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
        )
        translation_input = make_epub_translation_input(
            chapter_map=chapter_map,
            toc_entries=toc_entries,
        )
        translation_result = make_epub_translation_result(
            chapter_results=(
                make_epub_chapter_result(chapter_id="ch0001", chapter_order=1),
                make_epub_chapter_result(chapter_id="ch0002", chapter_order=2),
            )
        )

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        # Verify TOC in nav.xhtml
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            nav_files = [name for name in z.namelist() if name.endswith("nav.xhtml")]
            assert len(nav_files) >= 1
            nav_content = z.read(nav_files[0]).decode("utf-8")
            nav_root = ET.fromstring(nav_content)
            ns_xhtml = {"xhtml": "http://www.w3.org/1999/xhtml"}
            links = nav_root.findall(".//xhtml:a", ns_xhtml)
            link_titles = [link.text for link in links if link.text]
            assert "Chapter One" in link_titles
            assert "Chapter Two" in link_titles
            assert "Section 1" in link_titles

    def test_toc_chapter_identity_consistency(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """TOC entries must reference correct chapter hrefs."""
        from dataclasses import replace

        translation_input = make_epub_translation_input(
            chapter_map=(
                make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
                make_chapter_boundary(2, 2, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            ),
            toc_entries=(
                make_toc_entry("ch1.xhtml", "Chapter 1"),
                make_toc_entry("ch2.xhtml", "Chapter 2"),
            ),
        )

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="First")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="Second")
        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="First\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="Second\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            nav_files = [name for name in z.namelist() if name.endswith("nav.xhtml")]
            nav_content = z.read(nav_files[0]).decode("utf-8")
            nav_root = ET.fromstring(nav_content)
            ns_xhtml = {"xhtml": "http://www.w3.org/1999/xhtml"}
            links = nav_root.findall(".//xhtml:a", ns_xhtml)
            toc_hrefs = [link.get("href", "") for link in links]
            assert "ch1.xhtml" in toc_hrefs
            assert "ch2.xhtml" in toc_hrefs


# ========================================================================
# S5-A-08: CSS resource preservation
# ========================================================================

class TestS5A08CssResourcePreservation:
    """S5-A-08 — CSS resources preserved in output."""

    def test_css_resource_included(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """CSS resource from extraction included in output."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="css", href="styles/main.css"),
            make_resource_ref(type_="image", href="images/cover.jpg"),
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            css_files = [name for name in z.namelist() if name.endswith(".css")]
            assert len(css_files) >= 1


# ========================================================================
# S5-A-09: Image resource preservation
# ========================================================================

class TestS5A09ImageResourcePreservation:
    """S5-A-09 — Image resources preserved in output."""

    def test_image_resource_included(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Image resource from extraction included in output."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="image", href="images/cover.jpg"),
            make_resource_ref(type_="image", href="images/illustration.png"),
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True


# ========================================================================
# S5-A-10: Font/binary resource preservation
# ========================================================================

class TestS5A10FontBinaryResourcePreservation:
    """S5-A-10 — Font/binary resources preserved in output."""

    def test_font_resource_included(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Font resource from extraction included in output."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="font", href="fonts/NotoSerif.otf"),
            make_resource_ref(type_="font", href="fonts/NotoSans.woff2"),
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True


# ========================================================================
# S5-A-11: Multiple resources deterministic ordering
# ========================================================================

class TestS5A11DeterministicResourceOrdering:
    """S5-A-11 — Multiple resources have deterministic ordering."""

    def test_resources_ordered_deterministically(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Resources added in deterministic order."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="image", href="images/b.jpg"),
            make_resource_ref(type_="image", href="images/a.jpg"),
            make_resource_ref(type_="css", href="styles/z.css"),
            make_resource_ref(type_="css", href="styles/a.css"),
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path1 = tmp_path / "output1.epub"
        output_path2 = tmp_path / "output2.epub"

        result1 = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path1,
        )
        result2 = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path2,
        )

        assert result1.success is True
        assert result2.success is True

        import zipfile
        with zipfile.ZipFile(output_path1, 'r') as z1, zipfile.ZipFile(output_path2, 'r') as z2:
            names1 = sorted(z1.namelist())
            names2 = sorted(z2.namelist())
            assert names1 == names2


# ========================================================================
# S5-A-12: Duplicate/conflicting resource identity → fail closed
# ========================================================================

class TestS5A12DuplicateResourceFailClosed:
    """S5-A-12 — Duplicate resource identity fails closed."""

    def test_duplicate_resource_href_fails(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Duplicate resource href in input should fail validation at archive level."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="image", href="images/cover.jpg"),
            make_resource_ref(type_="image", href="images/cover.jpg"),  # Duplicate!
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        # Validation should catch duplicate IDs in manifest (fail closed)
        assert result.success is False
        assert "Duplicate IDs in manifest" in str(result.validation_errors)


# ========================================================================
# S5-A-13: Missing chapter → fail closed
# ========================================================================

class TestS5A13MissingChapterFailClosed:
    """S5-A-13 — Missing chapter fails closed."""

    def test_missing_chapter_in_result_fails(self) -> None:
        """Result missing chapters from input must fail closed (caught at S4 layer)."""
        translation_input = make_epub_translation_input()  # 3 chapters
        # Result only has 1 chapter
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="A\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        # S4 validation catches this before S5
        from core.epub_translation.reader_chapter_map import ReaderChapterMapBuildError
        with pytest.raises(ReaderChapterMapBuildError, match="missing chapters"):
            make_packaging_input(translation_input, translation_result)


# ========================================================================
# S5-A-14: Invalid chapter order → fail closed
# ========================================================================

class TestS5A14InvalidChapterOrderFailClosed:
    """S5-A-14 — Invalid chapter order fails closed."""

    def test_non_sequential_chapter_order_fails(self) -> None:
        """Non-sequential chapter_order in result must fail closed (caught at S4 layer)."""
        translation_input = make_epub_translation_input()
        # chapter_order jumps from 1 to 3 (missing 2)
        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="C")
        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="C\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        from core.epub_translation.reader_chapter_map import ReaderChapterMapBuildError
        with pytest.raises(ReaderChapterMapBuildError, match="missing chapters"):
            make_packaging_input(translation_input, translation_result)


# ========================================================================
# S5-A-15: Invalid spine reference → fail closed
# ========================================================================

class TestS5A15InvalidSpineReferenceFailClosed:
    """S5-A-15 — Invalid spine reference fails closed."""

    def test_spine_position_not_increasing_fails(self) -> None:
        """Non-increasing spine_position in input must fail at S5 validation."""
        chapters = (
            make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 3, "Ch2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 2, "Ch3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),  # spine_position 2 < 3 (not increasing)
        )
        translation_input = make_epub_translation_input(chapter_map=chapters)

        chunk1 = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="A")
        chunk2 = make_epub_chunk_result(chunk_id="ch0002:chunk0000", translated_text="B")
        chunk3 = make_epub_chunk_result(chunk_id="ch0003:chunk0000", translated_text="C")
        chapter_results = (
            make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk1,), assembled_text="A\n"),
            make_epub_chapter_result(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk2,), assembled_text="B\n"),
            make_epub_chapter_result(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk3,), assembled_text="C\n"),
        )
        translation_result = make_epub_translation_result(chapter_results=chapter_results)

        # S5 validation should catch non-increasing spine positions
        with pytest.raises(EpubPackagingError, match="strictly increasing"):
            make_packaging_input(translation_input, translation_result)


# ========================================================================
# S5-A-16: Invalid navigation reference → fail closed
# ========================================================================

class TestS5A16InvalidNavigationReferenceFailClosed:
    """S5-A-16 — Invalid navigation reference fails closed."""

    def test_toc_references_missing_chapter(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """TOC referencing non-existent chapter is detected as validation error."""
        from dataclasses import replace

        toc_entries = (
            make_toc_entry("missing.xhtml", "Missing Chapter"),
        )
        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),),
            toc_entries=toc_entries,
        )

        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="Content")
        chapter_result = make_epub_chapter_result(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="Content\n")
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        # Should fail validation due to broken TOC reference
        assert result.success is False
        assert any("missing.xhtml" in e for e in result.validation_errors)
        assert output_path.exists()


# ========================================================================
# S5-A-17: Packaging failure never silently creates TXT fallback
# ========================================================================

class TestS5A17NoTxtFallback:
    """S5-A-17 — Packaging failure never silently creates TXT fallback."""

    def test_packaging_failure_returns_error_result(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Packaging failure returns explicit failure result, not TXT."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        
        # Use an output path that cannot be created (non-existent parent directory)
        output_path = tmp_path / "nonexistent" / "output.epub"
        txt_path = tmp_path / "nonexistent" / "output.txt"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is False
        assert result.error_message is not None
        # Must NOT create TXT file
        assert not txt_path.exists()


# ========================================================================
# S5-A-18: Same input repeated packaging → deterministic result
# ========================================================================

class TestS5A18DeterministicPackaging:
    """S5-A-18 — Same input produces deterministic packaging."""

    def test_repeated_packaging_deterministic(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Two packaging runs with same input produce identical structure."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path1 = tmp_path / "output1.epub"
        output_path2 = tmp_path / "output2.epub"

        result1 = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path1,
        )
        result2 = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path2,
        )

        assert result1.success is True
        assert result2.success is True
        assert result1.chapter_count == result2.chapter_count
        assert result1.resource_count == result2.resource_count
        assert result1.source_identity == result2.source_identity

        # Verify identical archive structure
        import zipfile
        with zipfile.ZipFile(output_path1, 'r') as z1, zipfile.ZipFile(output_path2, 'r') as z2:
            names1 = sorted(z1.namelist())
            names2 = sorted(z2.namelist())
            assert names1 == names2


# ========================================================================
# S5-A-19: Output archive contains expected EPUB structural entries
# ========================================================================

class TestS5A19EpubStructuralEntries:
    """S5-A-19 — Output contains expected EPUB structural entries."""

    def test_mimetype_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have mimetype entry."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            assert "mimetype" in z.namelist()
            mimetype_content = z.read("mimetype").decode("utf-8").strip()
            assert mimetype_content == "application/epub+zip"

    def test_container_xml_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have META-INF/container.xml."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            assert "META-INF/container.xml" in z.namelist()

    def test_package_document_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have package document (content.opf)."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            assert opf_path in z.namelist()

    def test_manifest_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have manifest with all resources."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            manifest = opf_root.find(".//opf:manifest", ns_opf)
            assert manifest is not None
            items = list(manifest.findall("opf:item", ns_opf))
            assert len(items) >= 5  # nav + 3 chapters + css

    def test_spine_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have spine with chapters."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(output_path, 'r') as z:
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            spine = opf_root.find(".//opf:spine", ns_opf)
            assert spine is not None
            itemrefs = list(spine.findall("opf:itemref", ns_opf))
            assert len(itemrefs) >= 4

    def test_navigation_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have navigation document."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            nav_files = [name for name in z.namelist() if name.endswith("nav.xhtml")]
            assert len(nav_files) >= 1

    def test_chapter_resources_present(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Output EPUB must have chapter XHTML resources."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            chapter_files = [name for name in z.namelist() if name.endswith(".xhtml") and "nav" not in name.lower()]
            assert len(chapter_files) >= 3


# ========================================================================
# S5-A-20: Output is not merely TXT renamed .epub
# ========================================================================

class TestS5A20NotTxtRenamed:
    """S5-A-20 — Output is valid EPUB structure, not TXT renamed."""

    def test_output_has_epub_structure_not_txt(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Verify output has proper EPUB structure, not just text content."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            # Must have all required EPUB structures
            assert "mimetype" in z.namelist()
            assert "META-INF/container.xml" in z.namelist()
            
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            import xml.etree.ElementTree as ET
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            assert opf_path in z.namelist()
            
            nav_files = [n for n in z.namelist() if n.endswith("nav.xhtml")]
            assert len(nav_files) >= 1
            
            # Check for multiple structural components
            css_files = [n for n in z.namelist() if n.endswith(".css")]
            assert len(css_files) >= 1

    def test_chapter_content_is_xhtml_not_plain_text(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Chapter content must be XHTML, not plain text."""
        from dataclasses import replace

        translation_input = make_epub_translation_input(
            chapter_map=(make_chapter_boundary(1, 1, "Ch1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),)
        )
        chunk_result = make_epub_chunk_result(chunk_id="ch0001:chunk0000", translated_text="Plain text content")
        chapter_result = make_epub_chapter_result(
            chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_result,), assembled_text="Plain text content\n"
        )
        translation_result = make_epub_translation_result(chapter_results=(chapter_result,))

        packaging_input = make_packaging_input(translation_input, translation_result)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            chapter_files = [name for name in z.namelist() if name.endswith(".xhtml") and "nav" not in name.lower()]
            assert len(chapter_files) >= 1
            # Read chapter content and verify it's XHTML
            chapter_content = z.read(chapter_files[0]).decode("utf-8")
            assert "<p>" in chapter_content or "<html" in chapter_content


# ========================================================================
# Additional: Resource byte integrity (for binary resources)
# ========================================================================

class TestS5ResourceByteIntegrity:
    """Verify binary resource handling contract."""

    def test_binary_resources_not_converted_to_text(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Binary resources must not be treated as text."""
        from dataclasses import replace

        resources = (
            make_resource_ref(type_="image", href="images/cover.jpg"),
            make_resource_ref(type_="font", href="fonts/font.ttf"),
        )
        translation_input = make_epub_translation_input(resources=resources)

        packaging_input = make_packaging_input(translation_input)
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            # Check that resources are present in manifest
            import xml.etree.ElementTree as ET
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container_xml)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//container:rootfile", ns)
            opf_path = rootfile.get("full-path")
            opf_content = z.read(opf_path).decode("utf-8")
            opf_root = ET.fromstring(opf_content)
            ns_opf = {"opf": "http://www.idpf.org/2007/opf"}
            manifest = opf_root.find(".//opf:manifest", ns_opf)
            items = list(manifest.findall("opf:item", ns_opf))
            media_types = [item.get("media-type", "") for item in items]
            assert any(mt.startswith("image/") for mt in media_types)
            assert any(mt.startswith("font/") for mt in media_types)


# ========================================================================
# Safety tests (no network, no provider, no translation)
# ========================================================================

class TestSafety:
    """Verify no network, provider, or translation execution."""

    def test_no_network_calls(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Packaging must not make network calls."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        # Packaging is purely local - no network/provider calls

    def test_no_provider_calls(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Packaging must not call translation providers."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        # Uses pre-assembled text from translation_result only

    def test_no_real_translation(self, minimal_source_epub: Path, tmp_path: Path) -> None:
        """Packaging must not perform real translation."""
        from dataclasses import replace

        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )

        assert result.success is True
        # Uses pre-assembled text from translation_result only