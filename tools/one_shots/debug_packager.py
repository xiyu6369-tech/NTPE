from core.epub_translation.contract import (
    EpubMetadata, EpubChapterBoundary, ResourceRef, TocEntry,
    ExtractionManifest, EpubTranslationInput, EpubTranslationChunk,
    EpubChunkResult, EpubChapterResult, EpubTranslationResult,
)
from core.epub_translation.reader_chapter_map import build_epub_reader_chapter_map_with_metadata
from core.epub_translation.runtime.epub_packager import EpubPackagingInput, pack_epub_resource_aware
from tests.contract.test_s5_epub_packaging import make_resource_ref
from types import MappingProxyType
from pathlib import Path
import tempfile
import zipfile
import xml.etree.ElementTree as ET

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    source_epub = tmp_path / "source_with_image.epub"
    
    # Recreate the source EPUB with image
    fixture_path = Path("tests/contract/fixtures/test_image.png")
    image_bytes = fixture_path.read_bytes()
    
    with zipfile.ZipFile(source_epub, 'w') as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
        rootfiles = ET.SubElement(container, "rootfiles")
        rootfile = ET.SubElement(rootfiles, "rootfile", media_type="application/oebps-package+xml")
        rootfile.set("full-path", "OEBPS/content.opf")
        z.writestr("META-INF/container.xml", ET.tostring(container, encoding="unicode"))
        opf = ET.Element("package", xmlns="http://www.idpf.org/2007/opf", unique_identifier="bookid", version="3.0")
        metadata = ET.SubElement(opf, "metadata", xmlns_dc="http://purl.org/dc/elements/1.1/")
        ET.SubElement(metadata, "dc:identifier", id="bookid").text = "test-book"
        ET.SubElement(metadata, "dc:title").text = "Test Book"
        ET.SubElement(metadata, "dc:language").text = "ko"
        manifest = ET.SubElement(opf, "manifest")
        ET.SubElement(manifest, "item", id="nav", href="nav.xhtml", media_type="application/xhtml+xml", properties="nav")
        ET.SubElement(manifest, "item", id="ch1", href="chapter1.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch2", href="chapter2.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="ch3", href="chapter3.xhtml", media_type="application/xhtml+xml")
        ET.SubElement(manifest, "item", id="css", href="style.css", media_type="text/css")
        ET.SubElement(manifest, "item", id="img1", href="images/test_image.png", media_type="image/png")
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
        z.writestr("OEBPS/images/test_image.png", image_bytes)
    
    # Create packaging input
    metadata = EpubMetadata(title="Test Novel", author="Test Author", language="ko", identifier="test-id-123", publisher="Test Publisher", date="2024-01-01", raw=MappingProxyType({}))
    chapter_map = (
        EpubChapterBoundary(index=1, spine_position=1, title="Chapter 1", source_href="OEBPS/chapter1.xhtml", start_offset=0, end_offset=100, body_start_offset=30, body_end_offset=95, is_linear=True, word_count=50),
        EpubChapterBoundary(index=2, spine_position=2, title="Chapter 2", source_href="OEBPS/chapter2.xhtml", start_offset=100, end_offset=200, body_start_offset=130, body_end_offset=195, is_linear=True, word_count=50),
        EpubChapterBoundary(index=3, spine_position=3, title="Chapter 3", source_href="OEBPS/chapter3.xhtml", start_offset=200, end_offset=300, body_start_offset=230, body_end_offset=295, is_linear=True, word_count=50),
    )
    toc_entries = (
        TocEntry(href="chapter1.xhtml", title="Chapter 1", level=0),
        TocEntry(href="chapter2.xhtml", title="Chapter 2", level=0),
        TocEntry(href="chapter3.xhtml", title="Chapter 3", level=0),
    )
    translation_input = EpubTranslationInput(
        source_epub_path=source_epub,
        original_hash="a" * 64,
        extraction_status="success",
        warnings=(),
        metadata=metadata,
        chapter_map=chapter_map,
        resources=(make_resource_ref(type_="image", href="images/test_image.png"),),
        toc_entries=toc_entries,
        fixed_layout_info=None,
        extraction_manifest=ExtractionManifest(extractor_version="v1", extracted_at="2024-01-01", chapter_count=3, total_characters=300, total_words=150, warnings=(), resources=(), spine_item_count=3, nav_toc_entries=3, encoding_used="utf-8", parsing_duration_ms=100, fixed_layout=None),
    )
    chunk_results = (
        EpubChunkResult(chunk_id="ch0001:chunk0000", status="success", translated_text="번역1", error=None, attempt=1, qa_report=MappingProxyType({}), metadata=MappingProxyType({})),
        EpubChunkResult(chunk_id="ch0002:chunk0000", status="success", translated_text="번역2", error=None, attempt=1, qa_report=MappingProxyType({}), metadata=MappingProxyType({})),
        EpubChunkResult(chunk_id="ch0003:chunk0000", status="success", translated_text="번역3", error=None, attempt=1, qa_report=MappingProxyType({}), metadata=MappingProxyType({})),
    )
    chapter_results = (
        EpubChapterResult(chapter_id="ch0001", chapter_order=1, chunk_results=(chunk_results[0],), aggregate_status="success", success_count=1, failed_count=0, skipped_count=0, assembled_text="번역1\n"),
        EpubChapterResult(chapter_id="ch0002", chapter_order=2, chunk_results=(chunk_results[1],), aggregate_status="success", success_count=1, failed_count=0, skipped_count=0, assembled_text="번역2\n"),
        EpubChapterResult(chapter_id="ch0003", chapter_order=3, chunk_results=(chunk_results[2],), aggregate_status="success", success_count=1, failed_count=0, skipped_count=0, assembled_text="번역3\n"),
    )
    translation_result = EpubTranslationResult(aggregate_status="success", chapter_results=chapter_results, success_count=3, failed_count=0, skipped_count=0, session_id="test", resume_state_path=None)
    reader_result = build_epub_reader_chapter_map_with_metadata(translation_result, translation_input)
    packaging_input = EpubPackagingInput(reader_chapter_map_result=reader_result, translation_input=translation_input, translation_result=translation_result)
    
    output_path = tmp_path / "output.epub"
    result = pack_epub_resource_aware(packaging_input=packaging_input, output_path=output_path)
    print(f"Success: {result.success}")
    print(f"Errors: {result.validation_errors}")
    print(f"Error message: {result.error_message}")
    
    if output_path.exists():
        with zipfile.ZipFile(output_path, 'r') as z:
            print("Archive contents:", z.namelist())
            # Read OPF
            if "OEBPS/content.opf" in z.namelist():
                opf_content = z.read("OEBPS/content.opf").decode("utf-8")
                print("OPF content:")
                print(opf_content)
            # Read container
            container_xml = z.read("META-INF/container.xml").decode("utf-8")
            print("Container:", container_xml)
EOF