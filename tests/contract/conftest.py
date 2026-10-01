"""Pytest fixtures for S5 EPUB packaging tests."""

from __future__ import annotations

from pathlib import Path
import pytest
import zipfile
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.epub_translation.runtime.epub_packager import EpubPackagingInput


def _write_container_xml(z: zipfile.ZipFile) -> None:
    """Write META-INF/container.xml with correct full-path attribute."""
    container = ET.Element("container", version="1.0", xmlns="urn:oasis:names:tc:opendocument:xmlns:container")
    rootfiles = ET.SubElement(container, "rootfiles")
    rootfile = ET.SubElement(rootfiles, "rootfile", media_type="application/oebps-package+xml")
    rootfile.set("full-path", "OEBPS/content.opf")
    z.writestr("META-INF/container.xml", ET.tostring(container, encoding="unicode"))


def _write_opf(z: zipfile.ZipFile, extra_manifest_items: list[tuple[str, str, str]] | None = None) -> None:
    """Write OEBPS/content.opf with proper namespace declarations."""
    opf = ET.Element("package")
    opf.set("xmlns", "http://www.idpf.org/2007/opf")
    opf.set("unique-identifier", "bookid")
    opf.set("version", "3.0")
    metadata = ET.SubElement(opf, "metadata")
    ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}identifier", id="bookid").text = "test-book"
    ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}title").text = "Test Book"
    ET.SubElement(metadata, "{http://purl.org/dc/elements/1.1/}language").text = "ko"
    manifest = ET.SubElement(opf, "manifest")
    ET.SubElement(manifest, "item", id="nav", href="nav.xhtml", **{"media-type": "application/xhtml+xml"}, properties="nav")
    ET.SubElement(manifest, "item", id="ch1", href="chapter1.xhtml", **{"media-type": "application/xhtml+xml"})
    ET.SubElement(manifest, "item", id="ch2", href="chapter2.xhtml", **{"media-type": "application/xhtml+xml"})
    ET.SubElement(manifest, "item", id="ch3", href="chapter3.xhtml", **{"media-type": "application/xhtml+xml"})
    ET.SubElement(manifest, "item", id="css", href="style.css", **{"media-type": "text/css"})
    if extra_manifest_items:
        for item_id, href, media_type in extra_manifest_items:
            ET.SubElement(manifest, "item", id=item_id, href=href, **{"media-type": media_type})
    spine = ET.SubElement(opf, "spine")
    ET.SubElement(spine, "itemref", idref="nav")
    ET.SubElement(spine, "itemref", idref="ch1")
    ET.SubElement(spine, "itemref", idref="ch2")
    ET.SubElement(spine, "itemref", idref="ch3")
    z.writestr("OEBPS/content.opf", ET.tostring(opf, encoding="unicode"))


@pytest.fixture
def minimal_source_epub(tmp_path: Path) -> Path:
    """Create a minimal valid source EPUB for testing."""
    source_epub = tmp_path / "source.epub"

    with zipfile.ZipFile(source_epub, 'w') as z:
        # mimetype (must be first, uncompressed)
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        _write_container_xml(z)

        # OEBPS/content.opf
        _write_opf(z)

        # OEBPS/nav.xhtml
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

        # OEBPS/chapter1.xhtml, chapter2.xhtml, chapter3.xhtml
        for i in range(1, 4):
            ch = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
            head = ET.SubElement(ch, "head")
            ET.SubElement(head, "title").text = f"Chapter {i}"
            body = ET.SubElement(ch, "body")
            ET.SubElement(body, "p").text = f"Chapter {i} content"
            z.writestr(f"OEBPS/chapter{i}.xhtml", ET.tostring(ch, encoding="unicode"))

        # OEBPS/style.css
        z.writestr("OEBPS/style.css", "body { font-family: serif; }")

    return source_epub


@pytest.fixture
def source_epub_with_image(tmp_path: Path) -> Path:
    """Create a source EPUB with an image resource for byte integrity testing."""
    source_epub = tmp_path / "source_with_image.epub"

    # Read the test image fixture
    fixture_path = Path("tests/contract/fixtures/test_image.png")
    image_bytes = fixture_path.read_bytes()

    with zipfile.ZipFile(source_epub, 'w') as z:
        # mimetype (must be first, uncompressed)
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        _write_container_xml(z)

        # OEBPS/content.opf with image
        _write_opf(z, extra_manifest_items=[("img1", "images/test_image.png", "image/png")])

        # OEBPS/nav.xhtml
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

        # OEBPS/chapter1.xhtml, chapter2.xhtml, chapter3.xhtml
        for i in range(1, 4):
            ch = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
            head = ET.SubElement(ch, "head")
            ET.SubElement(head, "title").text = f"Chapter {i}"
            body = ET.SubElement(ch, "body")
            ET.SubElement(body, "p").text = f"Chapter {i} content"
            z.writestr(f"OEBPS/chapter{i}.xhtml", ET.tostring(ch, encoding="unicode"))

        # OEBPS/style.css
        z.writestr("OEBPS/style.css", "body { font-family: serif; }")

        # OEBPS/images/test_image.png
        z.writestr("OEBPS/images/test_image.png", image_bytes)

    return source_epub


@pytest.fixture
def image_fixture_bytes() -> bytes:
    """Return the test image bytes for comparison."""
    return Path("tests/contract/fixtures/test_image.png").read_bytes()


@pytest.fixture
def packaging_input_with_source(minimal_source_epub: Path) -> "EpubPackagingInput":
    """Create a packaging input with a real source EPUB."""
    from tests.contract.test_s5_epub_packaging import make_packaging_input
    from dataclasses import replace

    packaging_input = make_packaging_input()
    translation_input = packaging_input.translation_input
    translation_input = replace(translation_input, source_epub_path=minimal_source_epub)
    packaging_input = replace(packaging_input, translation_input=translation_input)

    return packaging_input


@pytest.fixture
def packaging_input_with_image(source_epub_with_image: Path) -> "EpubPackagingInput":
    """Create a packaging input with a source EPUB containing an image."""
    from tests.contract.test_s5_epub_packaging import make_packaging_input
    from dataclasses import replace

    packaging_input = make_packaging_input()
    translation_input = packaging_input.translation_input
    translation_input = replace(translation_input, source_epub_path=source_epub_with_image)
    packaging_input = replace(packaging_input, translation_input=translation_input)

    return packaging_input


@pytest.fixture
def packaging_input_with_references(source_epub_with_references: Path) -> "EpubPackagingInput":
    """Create a packaging input with a source EPUB containing comprehensive references."""
    from tests.contract.test_s5_epub_packaging import make_packaging_input
    from dataclasses import replace

    packaging_input = make_packaging_input()
    translation_input = packaging_input.translation_input
    translation_input = replace(translation_input, source_epub_path=source_epub_with_references)
    packaging_input = replace(packaging_input, translation_input=translation_input)

    return packaging_input


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Output EPUB path."""
    return tmp_path / "output.epub"


@pytest.fixture
def source_epub_with_references(tmp_path: Path) -> Path:
    """Create a source EPUB with comprehensive internal references for S5-C testing.
    
    Contains:
    - CSS reference (relative path)
    - Image reference (relative path)
    - Internal chapter link (chapter01 -> chapter02)
    - Same-document fragment link (#section-1)
    - Fragment target (id="section-1")
    """
    source_epub = tmp_path / "source_with_references.epub"

    # Read the test image fixture
    fixture_path = Path("tests/contract/fixtures/test_image.png")
    image_bytes = fixture_path.read_bytes()

    with zipfile.ZipFile(source_epub, 'w') as z:
        # mimetype (must be first, uncompressed)
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        _write_container_xml(z)

        # OEBPS/content.opf with all resources
        _write_opf(z, extra_manifest_items=[
            ("img1", "Images/image01.png", "image/png"),
        ])

        # OEBPS/nav.xhtml
        nav = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
        head = ET.SubElement(nav, "head")
        ET.SubElement(head, "title").text = "Navigation"
        body = ET.SubElement(nav, "body")
        nav_elem = ET.SubElement(body, "nav", epub_type="toc")
        ol = ET.SubElement(nav_elem, "ol")
        for i in range(1, 3):
            li = ET.SubElement(ol, "li")
            ET.SubElement(li, "a", href=f"chapter{i:02d}.xhtml").text = f"Chapter {i}"
        z.writestr("OEBPS/nav.xhtml", ET.tostring(nav, encoding="unicode"))

        # OEBPS/chapter01.xhtml - with CSS, image, chapter link, and fragment
        ch1 = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
        head1 = ET.SubElement(ch1, "head")
        ET.SubElement(head1, "title").text = "Chapter 1"
        ET.SubElement(head1, "link", rel="stylesheet", href="../Styles/main.css")
        body1 = ET.SubElement(ch1, "body")
        ET.SubElement(body1, "h1", id="section-1").text = "Chapter 1 Title"
        ET.SubElement(body1, "p").text = "This is the first chapter."
        ET.SubElement(body1, "img", src="../Images/image01.png", alt="Test Image")
        ET.SubElement(body1, "a", href="chapter2.xhtml").text = "Next Chapter"
        ET.SubElement(body1, "a", href="#section-1").text = "Link to Section 1"
        z.writestr("OEBPS/chapter1.xhtml", ET.tostring(ch1, encoding="unicode"))

        # OEBPS/chapter02.xhtml - with fragment target
        ch2 = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
        head2 = ET.SubElement(ch2, "head")
        ET.SubElement(head2, "title").text = "Chapter 2"
        ET.SubElement(head2, "link", rel="stylesheet", href="../Styles/main.css")
        body2 = ET.SubElement(ch2, "body")
        ET.SubElement(body2, "h1", id="section-1").text = "Chapter 2 Title"
        ET.SubElement(body2, "p").text = "This is the second chapter."
        z.writestr("OEBPS/chapter2.xhtml", ET.tostring(ch2, encoding="unicode"))

        # OEBPS/Styles/main.css
        z.writestr("OEBPS/Styles/main.css", "body { font-family: serif; }")

        # OEBPS/Images/image01.png
        z.writestr("OEBPS/Images/image01.png", image_bytes)

    return source_epub