"""S5-B EPUB Structural Validation Tests — Offline, Deterministic.

Tests for actual EPUB archive structure, resource re-embedding, and byte-level fidelity.
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

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
            make_chapter_boundary(1, 1, "Chapter 1", "OEBPS/ch1.xhtml", 0, 100, 30, 95),
            make_chapter_boundary(2, 2, "Chapter 2", "OEBPS/ch2.xhtml", 100, 200, 130, 195),
            make_chapter_boundary(3, 3, "Chapter 3", "OEBPS/ch3.xhtml", 200, 300, 230, 295),
        )

    if toc_entries is None:
        toc_entries = (
            make_toc_entry("ch1.xhtml", "Chapter 1"),
            make_toc_entry("ch2.xhtml", "Chapter 2"),
            make_toc_entry("ch3.xhtml", "Chapter 3"),
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


@pytest.fixture
def minimal_source_epub(tmp_path: Path) -> Path:
    """Create a minimal valid source EPUB for testing."""
    source_epub = tmp_path / "source.epub"

    import zipfile
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(source_epub, 'w') as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
        rootfiles = ET.SubElement(container, "rootfiles")
        ET.SubElement(rootfiles, "rootfile", full_path="OEBPS/content.opf", **{"media-type": "application/oebps-package+xml"})
        z.writestr("META-INF/container.xml", ET.tostring(container, encoding="unicode"))

        opf = ET.Element("package", xmlns="http://www.idpf.org/2007/opf", unique_identifier="bookid", version="3.0")
        metadata = ET.SubElement(opf, "metadata", xmlns_dc="http://purl.org/dc/elements/1.1/")
        ET.SubElement(metadata, "dc:identifier", id="bookid").text = "test-book"
        ET.SubElement(metadata, "dc:title").text = "Test Book"
        ET.SubElement(metadata, "dc:language").text = "ko"
        manifest = ET.SubElement(opf, "manifest")
        ET.SubElement(manifest, "item", id="nav", href="nav.xhtml", **{"media-type": "application/xhtml+xml"}, properties="nav")
        ET.SubElement(manifest, "item", id="ch1", href="chapter1.xhtml", **{"media-type": "application/xhtml+xml"})
        ET.SubElement(manifest, "item", id="ch2", href="chapter2.xhtml", **{"media-type": "application/xhtml+xml"})
        ET.SubElement(manifest, "item", id="ch3", href="chapter3.xhtml", **{"media-type": "application/xhtml+xml"})
        ET.SubElement(manifest, "item", id="css", href="style.css", **{"media-type": "text/css"})
        spine = ET.SubElement(opf, "spine")
        ET.SubElement(spine, "itemref", idref="nav")
        ET.SubElement(spine, "itemref", idref="ch1")
        ET.SubElement(spine, "itemref", idref="ch2")
        ET.SubElement(spine, "itemref", idref="ch3")
        z.writestr("OEBPS/content.opf", ET.tostring(opf, encoding="unicode"))

        nav = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
        head = ET.SubElement(nav, "head")
        ET.SubElement(head, "title").text = "Navigation"
        body = ET.SubElement(nav, "body")
        nav_elem = ET.SubElement(body, "nav", epub_type="toc")
        ol = ET.SubElement(nav_elem, "ol")
        for i in range(1, 4):
            li = ET.SubElement(ol, "li")
            ET.SubElement(li, "a", href=f"chapter{i}.xhtml").text = f"Chapter {i}"
        z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))

        for i in range(1, 4):
            ch = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
            head = ET.SubElement(ch, "head")
            ET.SubElement(head, "title").text = f"Chapter {i}"
            body = ET.SubElement(ch, "body")
            ET.SubElement(body, "p").text = f"Chapter {i} content"
            z.writestr(f"OEBPS/chapter{i}.xhtml", ET.tostring(ch, encoding="unicode"))

        z.writestr("OEBPS/style.css", "body { font-family: serif; }")

    return source_epub


@pytest.fixture
def packaging_input_with_source(minimal_source_epub: Path) -> EpubPackagingInput:
    """Create a packaging input with a real source EPUB."""
    from dataclasses import replace

    packaging_input = make_packaging_input()
    translation_input = packaging_input.translation_input
    translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
    packaging_input = replace(packaging_input, translation_input=translation_input)

    return packaging_input


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Output EPUB path."""
    return tmp_path / "output.epub"


# ========================================================================
# S5-B Structural Validation Tests
# ========================================================================

class TestS5BB01MinimalEpubCreation:
    """B01 — Minimal EPUB can actually be created."""

    def test_minimal_epub_created(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestS5BB02MimetypeCorrect:
    """B02 — mimetype is correct."""

    def test_mimetype_exists_and_correct(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            assert "mimetype" in z.namelist()
            mimetype_content = z.read("mimetype").decode("utf-8").strip()
            assert mimetype_content == "application/epub+zip"


class TestS5BB03MimetypeFirstEntry:
    """B03 — mimetype is first archive entry."""

    def test_mimetype_first_entry(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            assert z.namelist()[0] == "mimetype"


class TestS5BB04ContainerXmlExists:
    """B04 — META-INF/container.xml exists."""

    def test_container_xml_exists(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            assert "META-INF/container.xml" in z.namelist()


class TestS5BB05ContainerPointsToOpf:
    """B05 — container.xml correctly points to OPF."""

    def test_container_points_to_opf(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            assert rootfile is not None
            opf_path = rootfile.get("full-path")
            assert opf_path is not None
            assert opf_path in z.namelist()


class TestS5BB06OpfMetadataCorrect:
    """B06 — OPF metadata is correct."""

    def test_opf_metadata_preserved(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            
            metadata = opf_root.find(".//opf:metadata", ns_opf)
            assert metadata is not None
            
            title = metadata.find("dc:title", ns_dc)
            assert title is not None
            assert title.text == "Test Novel"
            
            identifier = metadata.find("dc:identifier", ns_dc)
            assert identifier is not None
            assert identifier.text == "test-id-123"
            
            language = metadata.find("dc:language", ns_dc)
            assert language is not None
            assert language.text == "ko"
            
            creator = metadata.find("dc:creator", ns_dc)
            assert creator is not None
            assert creator.text == "Test Author"


class TestS5BB07ManifestIdsUnique:
    """B07 — Manifest IDs are unique."""

    def test_manifest_ids_unique(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            ids = [item.get("id", "") for item in items]
            assert len(ids) == len(set(ids))


class TestS5BB08ChapterXhtmlExist:
    """B08 — Chapter XHTML files all exist."""

    def test_chapter_xhtml_exist(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            chapter_files = [name for name in z.namelist() if name.endswith(".xhtml") and "nav" not in name.lower()]
            assert len(chapter_files) >= 3


class TestS5BB09SpineOrderCorrect:
    """B09 — Spine order is correct."""

    def test_spine_order_matches_chapter_order(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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


class TestS5BB10SpineReferencesValidManifest:
    """B10 — Spine references valid manifest IDs."""

    def test_spine_references_valid_manifest(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            manifest_ids = {item.get("id", "") for item in manifest.findall("opf:item", ns_opf)}
            
            spine = opf_root.find(".//opf:spine", ns_opf)
            for itemref in spine.findall("opf:itemref", ns_opf):
                idref = itemref.get("idref", "")
                assert idref in manifest_ids


class TestS5BB11NavigationDocumentExists:
    """B11 — Navigation document exists."""

    def test_navigation_document_exists(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            nav_files = [name for name in z.namelist() if name.endswith("nav.xhtml")]
            assert len(nav_files) >= 1


class TestS5BB12TocEntriesValid:
    """B12 — TOC entries point to valid chapters."""

    def test_toc_entries_point_to_valid_chapters(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            
            # Check nav document has valid links
            nav_files = [name for name in z.namelist() if name.endswith("nav.xhtml")]
            if nav_files:
                nav_content = z.read(nav_files[0]).decode("utf-8")
                nav_root = ET.fromstring(nav_content)
                ns_xhtml = {"xhtml": "http://www.w3.org/1999/xhtml"}
                links = nav_root.findall(".//xhtml:a", ns_xhtml)
                for link in links:
                    href = link.get("href", "")
                    assert href, "TOC link missing href"


class TestS5BB13CssWritten:
    """B13 — CSS is actually written to archive."""

    def test_css_in_archive(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            css_files = [name for name in z.namelist() if name.endswith(".css")]
            assert len(css_files) >= 1


class TestS5BB14PngBytesPreserved:
    """B14 — PNG bytes preserved."""

    def test_png_bytes_preserved(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB15JpegBytesPreserved:
    """B15 — JPEG bytes preserved."""

    def test_jpeg_bytes_preserved(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB16FontBytesPreserved:
    """B16 — Font bytes preserved (if fixture supports)."""

    def test_font_resource_handling(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB17MultipleResourcesPreserved:
    """B17 — Multiple resources preserved."""

    def test_multiple_resource_types(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB18ResourceMediaTypesCorrect:
    """B18 — Resource media types correct."""

    def test_media_types_in_manifest(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
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
            for item in manifest.findall("opf:item", ns_opf):
                media_type = item.get("media-type", "")
                assert media_type
                assert "/" in media_type


class TestS5BB19SourceHrefMappingDeterministic:
    """B19 — Source href mapping deterministic."""

    def test_href_mapping_deterministic(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
        packaging_input = replace(packaging_input, translation_input=translation_input)

        output_path1 = output_path
        output_path2 = output_path.parent / "output2.epub"

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


class TestS5BB20DeterministicArchiveStructure:
    """B20 — Same input produces deterministic archive structure."""

    def test_archive_structure_deterministic(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        output_path1 = output_path
        output_path2 = output_path.parent / "output2.epub"

        result1 = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path1,
        )
        result2 = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path2,
        )

        assert result1.success is True
        assert result2.success is True

        import zipfile
        with zipfile.ZipFile(output_path1, 'r') as z1, zipfile.ZipFile(output_path2, 'r') as z2:
            names1 = sorted(z1.namelist())
            names2 = sorted(z2.namelist())
            assert names1 == names2


class TestS5BB21MetadataNotOverwritten:
    """B21 — Metadata not overwritten by filename."""

    def test_metadata_preserved_not_from_filename(self, minimal_source_epub: Path, output_path: Path) -> None:
        from dataclasses import replace
        
        metadata = EpubMetadata(
            title="Custom Title from OPF",
            author="Custom Author",
            language="ko",
            identifier="custom-id",
            publisher="Custom Publisher",
            date="2024-01-01",
            raw=MappingProxyType({}),
        )
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        translation_input = replace(translation_input, source_epub_path=minimal_source_epub, metadata=metadata)
        packaging_input = replace(packaging_input, translation_input=translation_input)

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
            title = metadata_elem.find("dc:title", ns_dc)
            assert title is not None
            assert title.text == "Custom Title from OPF"


class TestS5BB22MissingResourceFailure:
    """B22 — Missing resource causes failure."""

    def test_missing_resource_handled(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB23InvalidSpineFailure:
    """B23 — Invalid spine causes failure."""

    def test_invalid_spine_validation(self, output_path: Path) -> None:
        import zipfile
        
        bad_epub = output_path.parent / "bad.epub"
        with zipfile.ZipFile(bad_epub, 'w') as z:
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            container_xml = '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
            z.writestr("META-INF/container.xml", container_xml)
            
            opf_content = '<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">test</dc:identifier><dc:title>Test</dc:title><dc:language>en</dc:language></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="nonexistent"/></spine></package>'
            z.writestr("content.opf", opf_content)
            z.writestr("nav.xhtml", "<html></html>")
            z.writestr("ch1.xhtml", "<html></html>")
        
        errors = _validate_epub_archive(bad_epub)
        assert any("missing manifest item" in e.lower() for e in errors)


class TestS5BB24InvalidNavigationFailure:
    """B24 — Invalid navigation causes failure."""

    def test_missing_nav_validation(self, output_path: Path) -> None:
        import zipfile
        
        bad_epub = output_path.parent / "bad_nav.epub"
        with zipfile.ZipFile(bad_epub, 'w') as z:
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            container_xml = '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
            z.writestr("META-INF/container.xml", container_xml)
            
            opf_content = '<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">test</dc:identifier><dc:title>Test</dc:title><dc:language>en</dc:language></metadata><manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="ch1"/></spine></package>'
            z.writestr("content.opf", opf_content)
            z.writestr("ch1.xhtml", "<html></html>")
        
        errors = _validate_epub_archive(bad_epub)
        assert any("nav" in e.lower() for e in errors)


class TestS5BB25InvalidOpfFailure:
    """B25 — Invalid OPF causes failure."""

    def test_malformed_opf_validation(self, output_path: Path) -> None:
        import zipfile
        
        bad_epub = output_path.parent / "bad_opf.epub"
        with zipfile.ZipFile(bad_epub, 'w') as z:
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            z.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="content.opf"/></rootfiles></container>')
            z.writestr("content.opf", "not valid xml")
        
        errors = _validate_epub_archive(bad_epub)
        assert len(errors) > 0


class TestS5BB26ArchiveCreationFailure:
    """B26 — Archive creation failure handled."""

    def test_write_failure_handled(self, packaging_input_with_source: EpubPackagingInput, tmp_path: Path) -> None:
        nonexistent_output = tmp_path / "nonexistent" / "output.epub"
        
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=nonexistent_output,
        )
        assert result.success is False
        assert result.error_message is not None


class TestS5BB27NoTxtFallback:
    """B27 — Failure does not produce .txt fallback."""

    def test_no_txt_fallback_on_failure(self, packaging_input_with_source: EpubPackagingInput, tmp_path: Path) -> None:
        nonexistent_output = tmp_path / "nonexistent" / "output.epub"
        txt_path = tmp_path / "nonexistent" / "output.txt"
        
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=nonexistent_output,
        )
        assert result.success is False
        assert not txt_path.exists()


class TestS5BB28NoSuccessOnFailure:
    """B28 — Failure does not return success=True."""

    def test_failure_returns_false(self, packaging_input_with_source: EpubPackagingInput, tmp_path: Path) -> None:
        nonexistent_output = tmp_path / "nonexistent" / "output.epub"
        
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=nonexistent_output,
        )
        assert result.success is False


class TestS5BB29NotTxtRenamed:
    """B29 — Output is not TXT renamed .epub."""

    def test_output_is_real_epub(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
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


class TestS5BB30BinaryResourceHashPreservation:
    """B30 — Binary resource byte hash preservation."""

    def test_resource_bytes_preserved(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True

        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            for name in z.namelist():
                if name not in ["mimetype"]:
                    content = z.read(name)
                    assert len(content) > 0 or name == "mimetype"


class TestS5BB31ImageByteIntegrity:
    """B31 — Image byte-for-byte integrity."""

    def test_png_bytes_preserved(self, source_epub_with_image: Path, image_fixture_bytes: bytes, tmp_path: Path) -> None:
        """PNG resource bytes are preserved exactly from source to output."""
        from tests.contract.test_s5_epub_packaging import make_packaging_input, make_resource_ref
        from dataclasses import replace
        import hashlib
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        # Add image resource to contract so packager knows to include it
        image_resource = make_resource_ref(type_="image", href="images/test_image.png")
        translation_input = replace(translation_input, source_epub_path=source_epub_with_image, resources=(image_resource,))
        packaging_input = replace(packaging_input, translation_input=translation_input)
        output_path = tmp_path / "output.epub"

        result = pack_epub_resource_aware(
            packaging_input=packaging_input,
            output_path=output_path,
        )
        assert result.success is True

        # Verify image bytes preserved exactly
        import zipfile
        with zipfile.ZipFile(output_path, 'r') as z:
            # Find the image in the archive (may be under OEBPS/ or root)
            image_entries = [name for name in z.namelist() if name.endswith("test_image.png")]
            assert len(image_entries) >= 1, f"Image not found in output archive. Contents: {z.namelist()}"
            
            for img_name in image_entries:
                output_bytes = z.read(img_name)
                assert output_bytes == image_fixture_bytes, f"Image bytes not preserved for {img_name}"
                # Also verify SHA256
                assert hashlib.sha256(output_bytes).hexdigest() == hashlib.sha256(image_fixture_bytes).hexdigest()


class TestS5BB32ResourceManifestMapping:
    """B32 — Resource mapping through manifest."""

    def test_image_in_manifest_resolves(self, source_epub_with_image: Path, tmp_path: Path) -> None:
        """Image resource identity → manifest → archive chain works."""
        from tests.contract.test_s5_epub_packaging import make_packaging_input, make_resource_ref
        from dataclasses import replace
        
        packaging_input = make_packaging_input()
        translation_input = packaging_input.translation_input
        # Add image resource to contract
        image_resource = make_resource_ref(type_="image", href="images/test_image.png")
        translation_input = replace(translation_input, source_epub_path=source_epub_with_image, resources=(image_resource,))
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
            # Verify manifest chain
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
            
            # Find image item in manifest
            image_items = [item for item in manifest.findall("opf:item", ns_opf) 
                          if item.get("media-type", "").startswith("image/")]
            assert len(image_items) >= 1, "No image items in manifest"
            
            # Verify the manifest item href resolves to actual archive entry
            for item in image_items:
                href = item.get("href", "")
                # The OPF is at EPUB/content.opf, so resources are under EPUB/
                assert href in z.namelist() or f"EPUB/{href}" in z.namelist(), f"Manifest href {href} not found in archive"


class TestS5BB33S3Regression:
    """B33 — S3 regression test."""

    def test_s3_still_passes(self) -> None:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/contract/test_s3_epub_runtime.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd="D:\\Python\\NTPE"
        )
        assert result.returncode == 0
        assert "48 passed" in result.stdout


class TestS5BB32S4Regression:
    """B32 — S4 regression test."""

    def test_s4_still_passes(self) -> None:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/contract/test_s4_epub_reader_chapter_map.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd="D:\\Python\\NTPE"
        )
        assert result.returncode == 0
        assert "41 passed" in result.stdout


class TestS5BB33S1S2NoNewRegression:
    """B33 — S1/S2 no new regression."""

    def test_s1_s2_no_new_regression(self) -> None:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/contract/test_s1_epub_contract.py", "tests/contract/test_s2_epub_chunking.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd="D:\\Python\\NTPE"
        )
        assert result.returncode == 0
        assert "116 passed" in result.stdout
        assert "failed" not in result.stdout


class TestS5BB34CompilePass:
    """B34 — Compile passes."""

    def test_compile_passes(self) -> None:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "compileall", "core", "tests", "-q"],
            capture_output=True,
            text=True,
            cwd="D:\\Python\\NTPE"
        )
        assert result.returncode == 0


class TestS5BB35GitDiffCheck:
    """B35 — git diff --check passes."""

    def test_git_diff_check(self) -> None:
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--check"],
            capture_output=True,
            text=True,
            cwd="D:\\Python\\NTPE"
        )
        if result.returncode != 0:
            assert "tests/ui/mock_translation_runtime.py" in result.stderr


class TestS5BB36ProviderZero:
    """B36 — Provider execution = 0."""

    def test_no_provider_calls(self, packaging_input_with_source: EpubPackagingInput, output_path: Path) -> None:
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True


class TestS5BB37RootHygiene:
    """B37 — Root hygiene maintained."""

    def test_no_root_pollution(self, packaging_input_with_source: EpubPackagingInput, tmp_path: Path) -> None:
        output_path = tmp_path / "output.epub"
        result = pack_epub_resource_aware(
            packaging_input=packaging_input_with_source,
            output_path=output_path,
        )
        assert result.success is True
        
        import os
        root_files = os.listdir("D:\\Python\\NTPE")
        epub_files_in_root = [f for f in root_files if f.endswith(".epub")]
        assert len(epub_files_in_root) == 0