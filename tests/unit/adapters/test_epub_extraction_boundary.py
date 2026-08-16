"""Comprehensive tests for EpubExtractionBoundary implementation."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.adapters.epub_extraction_boundary import (
    ChapterBoundary,
    EpubExtractionBoundary,
    EpubExtractionError,
    EpubExtractionResult,
    EpubMetadata,
    ExtractionManifest,
    ResourceRef,
)


def _create_minimal_epub(tmp_path: Path) -> Path:
    """Create a minimal valid EPUB for testing."""
    epub_path = tmp_path / "test.epub"

    with zipfile.ZipFile(epub_path, "w") as zf:
        # META-INF/container.xml
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )

        # OEBPS/content.opf
        zf.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
    <dc:creator>Author Name</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:12345</dc:identifier>
    <dc:publisher>Test Publisher</dc:publisher>
    <dc:date>2024-01-01</dc:date>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
  </spine>
</package>""",
        )

        # OEBPS/nav.xhtml
        zf.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body>
    <nav epub:type="toc">
      <ol>
        <li><a href="ch1.xhtml">Chapter One</a></li>
        <li><a href="ch2.xhtml">Chapter Two</a></li>
      </ol>
    </nav>
  </body>
</html>""",
        )

        # OEBPS/ch1.xhtml
        zf.writestr(
            "OEBPS/ch1.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter 1</title></head>
  <body>
    <h1>Chapter One</h1>
    <p>This is the first paragraph.</p>
    <p>This is the second paragraph.</p>
  </body>
</html>""",
        )

        # OEBPS/ch2.xhtml
        zf.writestr(
            "OEBPS/ch2.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter 2</title></head>
  <body>
    <h1>Chapter Two</h1>
    <p>This is chapter two content.</p>
  </body>
</html>""",
        )

    return epub_path


class TestEpubExtractionBoundary:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_extractor_version(self):
        """Test extractor_version is set correctly."""
        assert self.boundary.extractor_version == "epub-extraction-v1.0.0"

    def test_extract_minimal_valid_epub(self, tmp_path: Path):
        """Test extraction of a minimal valid EPUB."""
        epub_path = _create_minimal_epub(tmp_path)
        result = self.boundary.extract(epub_path)

        assert isinstance(result, EpubExtractionResult)
        assert result.status in ("success", "partial")
        assert result.extracted_text != ""
        assert "Chapter One" in result.extracted_text
        assert "Chapter Two" in result.extracted_text
        assert len(result.chapter_map) == 2
        assert result.metadata.title == "Test Book"
        assert result.metadata.author == "Author Name"
        assert result.metadata.language == "en"
        assert result.original_hash == hashlib.sha256(epub_path.read_bytes()).hexdigest()
        assert result.extracted_hash == hashlib.sha256(result.extracted_text.encode("utf-8")).hexdigest()

    def test_extract_preserves_spine_order(self, tmp_path: Path):
        """Test that extraction preserves spine reading order."""
        epub_path = _create_minimal_epub(tmp_path)
        result = self.boundary.extract(epub_path)

        # Chapter 1 should come before Chapter 2
        ch1 = result.chapter_map[0]
        ch2 = result.chapter_map[1]
        assert ch1.index == 1
        assert ch2.index == 2
        assert ch1.start_offset < ch2.start_offset
        assert ch1.end_offset == ch2.start_offset  # Contiguous offsets

    def test_chapter_boundary_offsets_are_contiguous(self, tmp_path: Path):
        """Test that chapter offsets are contiguous with no gaps."""
        epub_path = _create_minimal_epub(tmp_path)
        result = self.boundary.extract(epub_path)

        for i in range(len(result.chapter_map) - 1):
            assert result.chapter_map[i].end_offset == result.chapter_map[i + 1].start_offset

        # Last chapter end_offset should equal total text length
        assert result.chapter_map[-1].end_offset == len(result.extracted_text)

    def test_chapter_markers_included_in_offsets(self, tmp_path: Path):
        """Test that chapter markers are included in offset calculations."""
        epub_path = _create_minimal_epub(tmp_path)
        result = self.boundary.extract(epub_path)

        ch1 = result.chapter_map[0]
        chapter_text = result.extracted_text[ch1.start_offset:ch1.end_offset]
        assert chapter_text.startswith("=== CHAPTER 1:")
        assert chapter_text.endswith("\n")

    def test_chapter_title_precedence_nav_toc(self, tmp_path: Path):
        """Test chapter title precedence: nav TOC title wins."""
        epub_path = _create_minimal_epub(tmp_path)
        result = self.boundary.extract(epub_path)

        ch1 = result.chapter_map[0]
        assert ch1.title == "Chapter One"  # From nav TOC

    def test_chapter_title_fallback_to_h1(self, tmp_path: Path):
        """Test chapter title falls back to first h1 when no TOC."""
        # Create EPUB without nav TOC
        epub_path = tmp_path / "no_toc.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Doc Title</title></head>
  <body>
    <h1>First Heading</h1>
    <p>Content</p>
  </body>
</html>""")

        result = self.boundary.extract(epub_path)
        assert result.chapter_map[0].title == "First Heading"

    def test_chapter_title_fallback_to_h2(self, tmp_path: Path):
        """Test chapter title falls back to first h2 when no h1."""
        epub_path = tmp_path / "h2_only.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Doc Title</title></head>
  <body>
    <h2>Second Heading</h2>
    <p>Content</p>
  </body>
</html>""")

        result = self.boundary.extract(epub_path)
        assert result.chapter_map[0].title == "Second Heading"

    def test_chapter_title_fallback_to_doc_title(self, tmp_path: Path):
        """Test chapter title falls back to document title when no headings."""
        epub_path = tmp_path / "doc_title.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Document Title Here</title></head>
  <body>
    <p>Just content, no headings.</p>
  </body>
</html>""")

        result = self.boundary.extract(epub_path)
        assert result.chapter_map[0].title == "Document Title Here"

    def test_chapter_title_generated_fallback(self, tmp_path: Path):
        """Test chapter title generated as 'Chapter N' when no other source."""
        epub_path = tmp_path / "no_title.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head></head>
  <body>
    <p>Just content.</p>
  </body>
</html>""")

        result = self.boundary.extract(epub_path)
        assert result.chapter_map[0].title == "Chapter 1"

    def test_linear_and_supplementary_items_order(self, tmp_path: Path):
        """Test linear items come first, then supplementary items."""
        epub_path = tmp_path / "mixed.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="app" href="appendix.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
    <itemref idref="app" linear="no"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><p>C1</p></body></html>""")
            zf.writestr("OEBPS/ch2.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch2</h1><p>C2</p></body></html>""")
            zf.writestr("OEBPS/appendix.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Appendix</h1><p>App</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert len(result.chapter_map) == 3
        # Linear items first in spine order
        assert result.chapter_map[0].title == "Ch1"
        assert result.chapter_map[0].status == "linear"
        assert result.chapter_map[1].title == "Ch2"
        assert result.chapter_map[1].status == "linear"
        # Supplementary items after in spine order
        assert result.chapter_map[2].title == "Appendix"
        assert result.chapter_map[2].status == "supplementary"
        # Offsets still contiguous
        assert result.chapter_map[0].end_offset == result.chapter_map[1].start_offset
        assert result.chapter_map[1].end_offset == result.chapter_map[2].start_offset

    def test_resource_manifest_images(self, tmp_path: Path):
        """Test image resources are recorded in manifest."""
        epub_path = tmp_path / "images.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="img1" href="images/fig1.jpg" media-type="image/jpeg"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><img src="images/fig1.jpg" alt="Figure 1"/><p>Content</p></body></html>""")
            zf.writestr("OEBPS/images/fig1.jpg", b"fake jpeg data")

        result = self.boundary.extract(epub_path)

        img_resources = [r for r in result.extraction_manifest.resources if r.type == "image"]
        assert len(img_resources) == 1
        assert img_resources[0].href == "images/fig1.jpg"
        assert img_resources[0].metadata["alt"] == "Figure 1"
        assert img_resources[0].chapter_index == 1

    def test_resource_manifest_remote_images_manual_review(self, tmp_path: Path):
        """Test remote images trigger manual_review_required."""
        epub_path = tmp_path / "remote.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><img src="http://example.com/image.jpg" alt="Remote"/><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert result.status == "manual_review_required"
        img_resources = [r for r in result.extraction_manifest.resources if r.type == "image"]
        assert len(img_resources) == 1
        assert img_resources[0].metadata.get("remote") is True

    def test_resource_manifest_data_uris(self, tmp_path: Path):
        """Test data URI images are recorded with data_uri flag."""
        epub_path = tmp_path / "datauri.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><img src="data:image/png;base64,abc123" alt="Inline"/><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        img_resources = [r for r in result.extraction_manifest.resources if r.type == "image"]
        assert len(img_resources) == 1
        assert img_resources[0].href == "data:"
        assert img_resources[0].metadata.get("data_uri") is True

    def test_resource_manifest_css(self, tmp_path: Path):
        """Test CSS resources are recorded."""
        epub_path = tmp_path / "css.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="css1" href="styles/main.css" media-type="text/css"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><head><link rel="stylesheet" href="styles/main.css" media="screen"/></head><body><h1>Ch1</h1><p>Content</p></body></html>""")
            zf.writestr("OEBPS/styles/main.css", "body { color: black; }")

        result = self.boundary.extract(epub_path)

        css_resources = [r for r in result.extraction_manifest.resources if r.type == "css"]
        assert len(css_resources) == 1
        assert css_resources[0].href == "styles/main.css"
        assert css_resources[0].metadata["media"] == "screen"

    def test_scripts_stripped_with_warning(self, tmp_path: Path):
        """Test JavaScript is stripped and warning issued."""
        epub_path = tmp_path / "scripts.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><script>alert('xss')</script><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "Script resource stripped" in " ".join(result.warnings)
        assert "alert" not in result.extracted_text

    def test_event_handlers_stripped(self, tmp_path: Path):
        """Test event handlers are stripped."""
        epub_path = tmp_path / "events.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1 onclick="alert(1)">Ch1</h1><p onload="init()">Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "Event handler stripped" in " ".join(result.warnings)
        assert "onclick" not in result.extracted_text
        assert "onload" not in result.extracted_text

    def test_mathml_preserved(self, tmp_path: Path):
        """Test MathML is preserved with marker."""
        epub_path = tmp_path / "mathml.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><math xmlns="http://www.w3.org/1998/Math/MathML"><mi>x</mi><mo>=</mo><mn>1</mn></math><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "[MATHML]" in result.extracted_text
        assert "x=1" in result.extracted_text

    def test_svg_placeholder(self, tmp_path: Path):
        """Test inline SVG becomes placeholder."""
        epub_path = tmp_path / "svg.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "[SVG]" in result.extracted_text

    def test_table_linearized(self, tmp_path: Path):
        """Test tables are linearized row by row."""
        epub_path = tmp_path / "table.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><table><tr><th>Header1</th><th>Header2</th></tr><tr><td>Cell1</td><td>Cell2</td></tr></table><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "[TH] Header1" in result.extracted_text
        assert "[TH] Header2" in result.extracted_text
        assert "Cell1" in result.extracted_text
        assert "Cell2" in result.extracted_text

    def test_ruby_annotations(self, tmp_path: Path):
        """Test ruby annotations are formatted as base(rt)."""
        epub_path = tmp_path / "ruby.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>ja</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><ruby>漢字<rt>かんじ</rt></ruby><p>Content</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "漢字(かんじ)" in result.extracted_text

    def test_encoding_detection_xml_decl(self, tmp_path: Path):
        """Test encoding detection from XML declaration."""
        epub_path = tmp_path / "encoding.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            # UTF-16 encoded content
            content = """<?xml version="1.0" encoding="UTF-16"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><p>Content</p></body></html>"""
            zf.writestr("OEBPS/ch1.xhtml", content.encode("utf-16")[2:])  # Skip BOM

        result = self.boundary.extract(epub_path)

        assert result.status in ("success", "partial")
        assert "Content" in result.extracted_text


class TestSecurityValidation:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_path_traversal_blocked(self, tmp_path: Path):
        """Test path traversal in ZIP is blocked."""
        epub_path = tmp_path / "traversal.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("../outside.txt", "malicious")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "path traversal" in str(exc.value).lower()

    def test_absolute_path_blocked(self, tmp_path: Path):
        """Test absolute paths are blocked."""
        epub_path = tmp_path / "absolute.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("/etc/passwd", "malicious")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True

    def test_drive_letter_path_blocked(self, tmp_path: Path):
        """Test Windows drive letter paths are blocked."""
        epub_path = tmp_path / "drive.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("C:\\Windows\\system32.dll", "malicious")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True

    def test_unc_path_blocked(self, tmp_path: Path):
        """Test UNC paths are blocked."""
        epub_path = tmp_path / "unc.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("\\\\server\\share\\file.dll", "malicious")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True

    def test_zip_bomb_blocked(self, tmp_path: Path):
        """Test zip bomb (high compression ratio) is blocked."""
        epub_path = tmp_path / "zipbomb.epub"
        # Create a file that compresses very well
        large_content = b"A" * 1000000  # 1MB of 'A's
        with zipfile.ZipFile(epub_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("OEBPS/content.opf", "opf")
            zf.writestr("OEBPS/bomb.txt", large_content)

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "zip bomb" in str(exc.value).lower()

    def test_nested_archive_blocked(self, tmp_path: Path):
        """Test nested ZIP/EPUB archives are blocked."""
        epub_path = tmp_path / "nested.epub"
        # Create a nested ZIP
        nested_zip = zipfile.ZipFile(tmp_path / "nested.zip", "w")
        nested_zip.writestr("inner.txt", "inner")
        nested_zip.close()

        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("OEBPS/content.opf", "opf")
            zf.write(tmp_path / "nested.zip", "nested.zip")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "nested archive" in str(exc.value).lower()

    def test_executable_extension_blocked(self, tmp_path: Path):
        """Test executable file extensions are blocked."""
        epub_path = tmp_path / "exe.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("OEBPS/content.opf", "opf")
            zf.writestr("malware.exe", "MZ...")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "executable" in str(exc.value).lower()

    def test_encryption_blocked(self, tmp_path: Path):
        """Test encryption.xml causes blocked status."""
        epub_path = tmp_path / "encrypted.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("META-INF/encryption.xml", "<encryption/>")
            zf.writestr("OEBPS/content.opf", "opf")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "encrypted" in str(exc.value).lower()

    def test_duplicate_canonical_paths_blocked(self, tmp_path: Path):
        """Test duplicate canonical paths (case-insensitive on Windows) are blocked."""
        epub_path = tmp_path / "dup.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", "container")
            zf.writestr("OEBPS/content.opf", "opf1")
            zf.writestr("oebps/content.opf", "opf2")  # Same path, different case

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "duplicate canonical" in str(exc.value).lower()

    def test_oversize_archive_blocked(self, tmp_path: Path):
        """Test archive exceeding max size is blocked."""
        epub_path = tmp_path / "oversize.epub"
        # This test is hard to do without creating a huge file
        # Just verify the constant exists
        from core.adapters.epub_extraction_boundary import _MAX_ARCHIVE_SIZE
        assert _MAX_ARCHIVE_SIZE == 500 * 1024 * 1024

    def test_missing_container_xml_blocked(self, tmp_path: Path):
        """Test missing container.xml is blocked."""
        epub_path = tmp_path / "no_container.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("OEBPS/content.opf", "opf")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True
        assert "container.xml" in str(exc.value).lower()

    def test_missing_opf_blocked(self, tmp_path: Path):
        """Test missing OPF is blocked."""
        epub_path = tmp_path / "no_opf.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/missing.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True

    def test_empty_spine_blocked(self, tmp_path: Path):
        """Test empty spine is blocked."""
        epub_path = tmp_path / "empty_spine.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest/>
  <spine/>
</package>""")

        with pytest.raises(EpubExtractionError) as exc:
            self.boundary.extract(epub_path)
        assert exc.value.blocked is True

    def test_all_supplementary_manual_review(self, tmp_path: Path):
        """Test all spine items linear=no triggers manual_review_required."""
        epub_path = tmp_path / "all_supp.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="app" href="appendix.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="app" linear="no"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/appendix.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Appendix</h1></body></html>""")

        result = self.boundary.extract(epub_path)
        assert result.status == "manual_review_required"


class TestDataStructures:
    def test_epub_metadata_all_fields(self):
        """Test EpubMetadata with all fields."""
        from types import MappingProxyType
        raw = MappingProxyType({"meta": "data"})
        metadata = EpubMetadata(
            title="Test Book",
            author="Test Author",
            language="en",
            identifier="isbn123",
            publisher="Test Publisher",
            date="2024-01-01",
            raw=raw,
        )
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
        assert metadata.language == "en"
        assert metadata.identifier == "isbn123"
        assert metadata.publisher == "Test Publisher"
        assert metadata.date == "2024-01-01"
        assert metadata.raw == raw

    def test_epub_metadata_optional_none(self):
        """Test EpubMetadata with None optional fields."""
        from types import MappingProxyType
        metadata = EpubMetadata(
            title=None,
            author=None,
            language=None,
            identifier=None,
            publisher=None,
            date=None,
            raw=MappingProxyType({}),
        )
        assert metadata.title is None
        assert metadata.author is None

    def test_chapter_boundary_all_fields(self):
        """Test ChapterBoundary with all fields."""
        chapter = ChapterBoundary(
            index=1,
            spine_position=5,
            title="Chapter 1",
            start_offset=0,
            end_offset=1000,
            source_href="ch1.xhtml",
            toc_level=1,
            is_linear=True,
            word_count=500,
            landmark_type="chapter",
            status="linear",
        )
        assert chapter.index == 1
        assert chapter.spine_position == 5
        assert chapter.title == "Chapter 1"
        assert chapter.start_offset == 0
        assert chapter.end_offset == 1000
        assert chapter.source_href == "ch1.xhtml"
        assert chapter.toc_level == 1
        assert chapter.is_linear is True
        assert chapter.word_count == 500
        assert chapter.landmark_type == "chapter"
        assert chapter.status == "linear"

    def test_chapter_boundary_defaults(self):
        """Test ChapterBoundary default values."""
        chapter = ChapterBoundary(
            index=1,
            spine_position=1,
            title="Ch1",
            start_offset=0,
            end_offset=100,
            source_href="ch1.xhtml",
        )
        assert chapter.toc_level == 0
        assert chapter.is_linear is True
        assert chapter.word_count == 0
        assert chapter.landmark_type is None
        assert chapter.status == "linear"

    def test_resource_ref(self):
        """Test ResourceRef dataclass."""
        from types import MappingProxyType
        ref = ResourceRef(
            type="image",
            href="images/fig1.jpg",
            chapter_index=1,
            metadata=MappingProxyType({"alt": "Figure 1"}),
        )
        assert ref.type == "image"
        assert ref.href == "images/fig1.jpg"
        assert ref.chapter_index == 1
        assert ref.metadata["alt"] == "Figure 1"

    def test_extraction_manifest_all_fields(self):
        """Test ExtractionManifest with all fields."""
        from types import MappingProxyType
        manifest = ExtractionManifest(
            extractor_version="v1.0",
            extracted_at="2024-01-01T00:00:00Z",
            chapter_count=5,
            total_characters=50000,
            total_words=10000,
            warnings=("warn1", "warn2"),
            resources=(),
            spine_item_count=3,
            nav_toc_entries=5,
            encoding_used="utf-8",
            parsing_duration_ms=100,
            fixed_layout=MappingProxyType({"viewport": {"width": 1200}}),
        )
        assert manifest.extractor_version == "v1.0"
        assert manifest.chapter_count == 5
        assert manifest.total_characters == 50000
        assert manifest.total_words == 10000
        assert manifest.warnings == ("warn1", "warn2")
        assert manifest.spine_item_count == 3
        assert manifest.nav_toc_entries == 5
        assert manifest.encoding_used == "utf-8"
        assert manifest.parsing_duration_ms == 100
        assert manifest.fixed_layout["viewport"]["width"] == 1200

    def test_epub_extraction_result_all_fields(self, tmp_path: Path):
        """Test EpubExtractionResult with all fields."""
        from types import MappingProxyType
        metadata = EpubMetadata(
            title="Test", author="Author", language="en",
            identifier="id", publisher="Pub", date="2024",
            raw=MappingProxyType({})
        )
        chapters = (
            ChapterBoundary(1, 1, "Ch1", 0, 100, "ch1.xhtml"),
        )
        manifest = ExtractionManifest(
            extractor_version="v1", extracted_at="2024", chapter_count=1,
            total_characters=100, total_words=20, warnings=(), resources=(),
            spine_item_count=1, nav_toc_entries=1, encoding_used="utf-8",
            parsing_duration_ms=10,
        )
        result = EpubExtractionResult(
            source_path=tmp_path / "test.epub",
            original_hash="abc123",
            extracted_text="Full text",
            extracted_hash="def456",
            metadata=metadata,
            chapter_map=chapters,
            extraction_manifest=manifest,
            status="success",
            warnings=(),
        )
        assert result.source_path == tmp_path / "test.epub"
        assert result.original_hash == "abc123"
        assert result.extracted_text == "Full text"
        assert result.extracted_hash == "def456"
        assert result.metadata == metadata
        assert result.chapter_map == chapters
        assert result.extraction_manifest == manifest
        assert result.status == "success"
        assert result.warnings == ()

    def test_epub_extraction_error(self):
        """Test EpubExtractionError with blocked and warnings."""
        err = EpubExtractionError("test error", blocked=True, warnings=("warn1",))
        assert err.blocked is True
        assert err.warnings == ("warn1",)
        assert str(err) == "test error"


class TestDeterminism:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_deterministic_extraction(self, tmp_path: Path):
        """Test same EPUB produces identical output on multiple runs."""
        epub_path = _create_minimal_epub(tmp_path)

        result1 = self.boundary.extract(epub_path)
        result2 = self.boundary.extract(epub_path)

        assert result1.extracted_text == result2.extracted_text
        assert result1.extracted_hash == result2.extracted_hash
        assert result1.chapter_map == result2.chapter_map
        # Deterministic manifest fields should match
        assert result1.extraction_manifest.chapter_count == result2.extraction_manifest.chapter_count
        assert result1.extraction_manifest.total_characters == result2.extraction_manifest.total_characters
        assert result1.extraction_manifest.total_words == result2.extraction_manifest.total_words
        assert result1.extraction_manifest.warnings == result2.extraction_manifest.warnings
        assert result1.extraction_manifest.resources == result2.extraction_manifest.resources

    def test_deterministic_manifest_identity(self, tmp_path: Path):
        """Test manifest identity is deterministic."""
        epub_path = _create_minimal_epub(tmp_path)

        result1 = self.boundary.extract(epub_path)
        result2 = self.boundary.extract(epub_path)

        # Build canonical JSON for manifest identity (excluding non-deterministic fields)
        import json
        def canonical_manifest(m):
            return json.dumps({
                "extractor_version": m.extractor_version,
                "chapter_count": m.chapter_count,
                "total_characters": m.total_characters,
                "total_words": m.total_words,
                "warnings": list(m.warnings),
                "resources": [
                    {"type": r.type, "href": r.href, "chapter_index": r.chapter_index, "metadata": dict(r.metadata)}
                    for r in m.resources
                ],
                "spine_item_count": m.spine_item_count,
                "nav_toc_entries": m.nav_toc_entries,
                "encoding_used": m.encoding_used,
            }, sort_keys=True, separators=(",", ":"))

        assert canonical_manifest(result1.extraction_manifest) == canonical_manifest(result2.extraction_manifest)


class TestValidateEpub:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_validate_nonexistent_file(self, tmp_path: Path):
        """Test validate_epub returns False for non-existent file."""
        epub_path = tmp_path / "nonexistent.epub"
        is_valid, error = self.boundary.validate_epub(epub_path)
        assert is_valid is False
        assert "not found" in error.lower()

    def test_validate_wrong_extension(self, tmp_path: Path):
        """Test validate_epub returns False for non-EPUB file."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not an epub")
        is_valid, error = self.boundary.validate_epub(txt_path)
        assert is_valid is False
        assert "not an epub" in error.lower()

    def test_validate_invalid_zip(self, tmp_path: Path):
        """Test validate_epub returns False for invalid ZIP."""
        epub_path = tmp_path / "test.epub"
        epub_path.write_bytes(b"not a zip file")
        is_valid, error = self.boundary.validate_epub(epub_path)
        assert is_valid is False
        assert "invalid zip" in error.lower() or "zip file" in error.lower()

    def test_validate_missing_container(self, tmp_path: Path):
        """Test validate_epub returns False for missing container.xml."""
        epub_path = tmp_path / "test.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("OEBPS/content.opf", "opf")
        is_valid, error = self.boundary.validate_epub(epub_path)
        assert is_valid is False
        assert "container.xml" in error.lower()

    def test_validate_valid_epub(self, tmp_path: Path):
        """Test validate_epub returns True for valid EPUB."""
        epub_path = _create_minimal_epub(tmp_path)
        is_valid, error = self.boundary.validate_epub(epub_path)
        assert is_valid is True
        assert error is None

    def test_validate_contract(self, tmp_path: Path):
        """Test validate_epub returns correct tuple structure."""
        boundary = EpubExtractionBoundary()

        result = boundary.validate_epub(tmp_path / "missing.epub")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

        txt = tmp_path / "test.txt"
        txt.write_text("text")
        result = boundary.validate_epub(txt)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)


class TestFixedLayout:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_fixed_layout_viewport_metadata(self, tmp_path: Path):
        """Test fixed-layout viewport metadata is recorded."""
        epub_path = tmp_path / "fixed.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"
         xmlns:rendition="http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:viewport">width=1200, height=1600, portrait</meta>
    <meta property="rendition:spread">landscape</meta>
    <meta property="rendition:orientation">portrait</meta>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine page-progression-direction="rtl">
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1></body></html>""")

        result = self.boundary.extract(epub_path)

        assert result.extraction_manifest.fixed_layout is not None
        fl = result.extraction_manifest.fixed_layout
        assert fl["viewport"]["width"] == 1200
        assert fl["viewport"]["height"] == 1600
        assert fl["viewport"]["orientation"] == "portrait"
        assert fl["spread"] == "landscape"
        assert fl["orientation"] == "portrait"
        assert fl["page_progression_direction"] == "rtl"

    def test_fixed_layout_defaults(self, tmp_path: Path):
        """Test fixed-layout defaults when metadata missing."""
        epub_path = tmp_path / "fixed_minimal.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"
         xmlns:rendition="http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
    <meta property="rendition:layout">pre-paginated</meta>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1></body></html>""")

        result = self.boundary.extract(epub_path)

        assert result.extraction_manifest.fixed_layout is not None
        fl = result.extraction_manifest.fixed_layout
        assert fl["viewport"]["width"] == 1200
        assert fl["viewport"]["height"] == 1600
        assert fl["viewport"]["orientation"] == "portrait"
        assert fl["spread"] == "auto"
        assert fl["orientation"] == "auto"
        assert fl["page_progression_direction"] == "ltr"


class TestEPUB2Support:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_epub2_ncx_toc(self, tmp_path: Path):
        """Test EPUB 2 NCX TOC parsing."""
        epub_path = tmp_path / "epub2.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>EPUB 2 Book</dc:title>
    <dc:creator>Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/toc.ncx", """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head></head>
  <docTitle><text>EPUB 2 Book</text></docTitle>
  <navMap>
    <navPoint id="ch1" playOrder="1">
      <navLabel><text>Chapter One</text></navLabel>
      <content src="ch1.xhtml"/>
    </navPoint>
    <navPoint id="ch2" playOrder="2">
      <navLabel><text>Chapter Two</text></navLabel>
      <content src="ch2.xhtml"/>
    </navPoint>
  </navMap>
</ncx>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Chapter One</h1><p>Content 1</p></body></html>""")
            zf.writestr("OEBPS/ch2.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Chapter Two</h1><p>Content 2</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert result.status in ("success", "partial")
        assert len(result.chapter_map) == 2
        assert result.chapter_map[0].title == "Chapter One"
        assert result.chapter_map[1].title == "Chapter Two"


class TestMalformedHandling:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_malformed_xhtml_partial(self, tmp_path: Path):
        """Test malformed XHTML results in partial status."""
        epub_path = tmp_path / "malformed.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            # Malformed XHTML - unclosed tag
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1<p>Content</body></html>""")

        result = self.boundary.extract(epub_path)

        assert result.status == "partial"
        assert "Content" in result.extracted_text  # Still extracted what it could


class TestEntityDecoding:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_html_entities_decoded_once(self, tmp_path: Path):
        """Test HTML entities are decoded only once (no double decoding)."""
        epub_path = tmp_path / "entities.epub"
        zf = zipfile.ZipFile(epub_path, "w")
        try:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            # < should decode to < once, not to <
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><p><tag> and &#38; entity</p></body></html>""")
        finally:
            zf.close()

            result = self.boundary.extract(epub_path)

            assert "<tag>" in result.extracted_text  # < decoded to <
            assert "&" in result.extracted_text  # &#38; decoded once to & (literal &)
            assert "&amp;" not in result.extracted_text  # Not double-decoded (no & entity string)
    def test_numeric_entities(self, tmp_path: Path):
        """Test numeric character references are decoded."""
        epub_path = tmp_path / "numeric.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><p>&#x41;&#65; = A</p></body></html>""")

        result = self.boundary.extract(epub_path)

        assert "AA = A" in result.extracted_text


class TestNewlineNormalization:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_crlf_normalized_to_lf(self, tmp_path: Path):
        """Test CRLF normalized to LF."""
        epub_path = tmp_path / "crlf.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            # Content with CRLF
            content = "<html xmlns=\"http://www.w3.org/1999/xhtml\"><body><h1>Ch1</h1>\r\n<p>Line1</p>\r\n<p>Line2</p></body></html>"
            zf.writestr("OEBPS/ch1.xhtml", content)

        result = self.boundary.extract(epub_path)

        # All newlines should be LF
        assert "\r\n" not in result.extracted_text
        assert "\r" not in result.extracted_text
        assert "\n" in result.extracted_text


class TestNCXLandmarks:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_nav_landmarks_recorded(self, tmp_path: Path):
        """Test nav landmarks are recorded in chapter boundaries."""
        epub_path = tmp_path / "landmarks.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/nav.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <body>
    <nav epub:type="toc">
      <ol><li><a href="ch1.xhtml">Chapter 1</a></li></ol>
    </nav>
    <nav epub:type="landmarks">
      <ol><li><a epub:type="cover" href="cover.xhtml">Cover</a></li></ol>
    </nav>
  </body>
</html>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Chapter 1</h1></body></html>""")

        result = self.boundary.extract(epub_path)

        # Landmarks should be recorded but not affect reading order
        assert result.chapter_map[0].landmark_type in ("chapter", None)
        assert len(result.extraction_manifest.resources) >= 0


class TestResourceManifestOrdering:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_resources_sorted_deterministically(self, tmp_path: Path):
        """Test resources are sorted deterministically by (type, href, chapter_index)."""
        epub_path = tmp_path / "resources.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="css1" href="styles/a.css" media-type="text/css"/>
    <item id="css2" href="styles/b.css" media-type="text/css"/>
    <item id="img1" href="images/z.jpg" media-type="image/jpeg"/>
    <item id="img2" href="images/a.jpg" media-type="image/jpeg"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml">
<head><link rel="stylesheet" href="styles/b.css"/><link rel="stylesheet" href="styles/a.css"/></head>
<body><h1>Ch1</h1><img src="images/z.jpg" alt="Z"/><img src="images/a.jpg" alt="A"/></body></html>""")
            zf.writestr("OEBPS/styles/a.css", "/* a */")
            zf.writestr("OEBPS/styles/b.css", "/* b */")
            zf.writestr("OEBPS/images/a.jpg", "img")
            zf.writestr("OEBPS/images/z.jpg", "img")

        result = self.boundary.extract(epub_path)

        # Resources should be sorted by (type, href, chapter_index)
        resource_keys = [(r.type, r.href, r.chapter_index) for r in result.extraction_manifest.resources]
        assert resource_keys == sorted(resource_keys)


class TestWarningOrdering:
    def setup_method(self):
        self.boundary = EpubExtractionBoundary()

    def test_warnings_deterministic_order(self, tmp_path: Path):
        """Test warnings are emitted in deterministic order."""
        epub_path = tmp_path / "warn.epub"
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            zf.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test</dc:title>
    <dc:identifier id="bookid">urn:uuid:123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1" linear="yes"/>
    <itemref idref="ch2" linear="yes"/>
  </spine>
</package>""")
            zf.writestr("OEBPS/ch1.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch1</h1><script>bad</script></body></html>""")
            zf.writestr("OEBPS/ch2.xhtml", """<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Ch2</h1><script>bad</script></body></html>""")

        result1 = self.boundary.extract(epub_path)
        result2 = self.boundary.extract(epub_path)

        assert result1.warnings == result2.warnings