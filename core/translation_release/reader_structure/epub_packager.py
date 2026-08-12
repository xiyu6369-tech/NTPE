from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap


_CHAPTER_PATTERN = re.compile(r"(?:第\s*\d+\s*章|Chapter\s+\d+|CHAPTER\s+\d+)")


def _extract_chapter_title(text: str, fallback: str) -> str:
    """Extract chapter title from explicit marker in text."""
    match = _CHAPTER_PATTERN.search(text)
    if match:
        return match.group(0).replace(" ", "")
    return fallback


def _slice_chapter_text(txt_body: str, chapter: ChapterBoundary) -> str:
    """Slice chapter text from txt_body using 0-based end-exclusive positions."""
    return txt_body[chapter.start_position:chapter.end_position]


def _escape_xhtml(text: str) -> str:
    """Escape XML/HTML special characters for safe XHTML content.

    Only escapes presentation layer; does not modify original text.
    """
    return html.escape(text, quote=False)


def _paragraphs_to_xhtml(text: str) -> str:
    """Convert TXT paragraphs to XHTML <p> elements.

    Preserves exact text content; only wraps paragraphs in <p> tags
    with XML escaping applied for presentation safety.
    """
    if not text.strip():
        return "<p></p>"

    paragraphs = text.split("\n\n")
    xhtml_parts: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if para:
            escaped = _escape_xhtml(para)
            xhtml_parts.append(f"<p>{escaped}</p>")
        else:
            xhtml_parts.append("<p></p>")
    return "\n".join(xhtml_parts)


def _build_chapter_xhtml(
    chapter: ChapterBoundary,
    txt_body: str,
    chapter_index: int,
) -> tuple[str, str]:
    """Build XHTML content for a single chapter.

    Returns:
        (file_name, xhtml_content)
    """
    chapter_text = _slice_chapter_text(txt_body, chapter)

    title = _extract_chapter_title(chapter_text, chapter.chapter_title)

    xhtml_body = _paragraphs_to_xhtml(chapter_text)

    file_name = f"chapter_{chapter_index:03d}.xhtml"

    xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-TW">
<head>
    <meta charset="utf-8"/>
    <title>{_escape_xhtml(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    {xhtml_body}
</body>
</html>"""

    return file_name, xhtml_content


def _validate_chapter_map_integrity(chapters: list[ChapterBoundary], txt_body: str) -> None:
    """Validate chapter map integrity before EPUB generation.

    Raises ValueError if any validation fails.
    """
    if not chapters:
        if txt_body:
            raise ValueError("Chapter map is empty but txt_body is not empty")
        return

    if chapters[0].start_position != 0:
        raise ValueError(f"First chapter must start at position 0, got {chapters[0].start_position}")

    if chapters[-1].end_position != len(txt_body):
        raise ValueError(
            f"Last chapter end_position ({chapters[-1].end_position}) "
            f"must equal txt_body length ({len(txt_body)})"
        )

    for i, chapter in enumerate(chapters):
        if not (0 <= chapter.start_position < chapter.end_position <= len(txt_body)):
            raise ValueError(
                f"Chapter {chapter.chapter_id} has invalid position: "
                f"[{chapter.start_position}, {chapter.end_position}) "
                f"for txt_body length {len(txt_body)}"
            )

        if i > 0:
            prev = chapters[i - 1]
            if prev.end_position != chapter.start_position:
                raise ValueError(
                    f"Gap or overlap between chapters: "
                    f"chapter {i - 1} ends at {prev.end_position}, "
                    f"chapter {i} starts at {chapter.start_position}"
                )

    reconstructed = "".join(
        txt_body[c.start_position:c.end_position]
        for c in chapters
    )
    if reconstructed != txt_body:
        raise ValueError("Content preservation invariant violated: reconstructed text != original text")


def _build_nav_document(chapters: list[ChapterBoundary], txt_body: str, novel_title: str) -> str:
    """Build EPUB navigation document (nav.xhtml)."""
    nav_items: list[str] = []
    for i, chapter in enumerate(chapters, start=1):
        chapter_text = _slice_chapter_text(txt_body, chapter)
        title = _extract_chapter_title(chapter_text, chapter.chapter_title)
        file_name = f"chapter_{i:03d}.xhtml"
        nav_items.append(f'        <li><a href="{file_name}">{_escape_xhtml(title)}</a></li>')

    nav_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-TW">
<head>
    <meta charset="utf-8"/>
    <title>目錄</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>目錄</h1>
        <ol>
{chr(10).join(nav_items)}
        </ol>
    </nav>
</body>
</html>"""

    return nav_content


def _build_css() -> str:
    """Build basic CSS for EPUB readability."""
    return """@charset "utf-8";

body {
    font-family: "Noto Serif CJK TC", "PingFang TC", "Microsoft JhengHei", serif;
    line-height: 1.8;
    margin: 2em 1.5em;
    text-align: justify;
}

p {
    margin: 0.5em 0;
    text-indent: 2em;
}

p:first-child {
    text-indent: 0;
}

h1 {
    text-align: center;
    margin: 2em 0 1em;
    font-size: 1.5em;
    font-weight: bold;
}

nav ol {
    list-style: none;
    padding: 0;
}

nav li {
    margin: 0.5em 0;
}

nav a {
    text-decoration: none;
    color: #333;
}

nav a:hover {
    text-decoration: underline;
}
"""


def pack_epub(
    *,
    txt_body: str,
    reader_chapter_map: ReaderChapterMap,
    novel_id: str,
    output_path: Path,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Package EPUB from RM-8.3 TXT body using Phase 1 ReaderChapterMap.

    This is a READ-ONLY packaging operation. The txt_body is NOT modified.

    Args:
        txt_body: The final RM-8.3 TXT body (source of truth, not modified)
        reader_chapter_map: Immutable chapter mapping from Phase 1
        novel_id: Novel identifier for EPUB metadata
        output_path: Output EPUB file path
        metadata: Optional additional metadata (title, author, etc.)

    Returns:
        True on success, False if EPUB dependency unavailable or I/O error

    Raises:
        ValueError: If chapter map validation fails (deterministic failure)
    """
    try:
        from ebooklib import epub
    except ImportError:
        return False  # graceful: format unavailable

    chapters = list(reader_chapter_map.chapters)

    _validate_chapter_map_integrity(chapters, txt_body)

    book = epub.EpubBook()
    book.set_identifier(novel_id)

    meta = metadata or {}
    title = meta.get("title", novel_id)
    author = meta.get("author", "未知作者")
    translator = meta.get("translator", "NTPE Translation Engine")
    date = meta.get("date", "")
    pipeline_version = meta.get("pipeline_version", "NTPE_RM84_v1")

    book.set_title(title)
    book.set_language("zh-TW")
    book.add_author(author)

    book.add_metadata("DC", "translator", translator)
    if date:
        book.add_metadata("DC", "date", date)
    book.add_metadata("DC", "pipeline", pipeline_version)

    spine_items: list = ["nav"]
    toc_items: list = []
    chapter_files: list[tuple[str, epub.EpubHtml]] = []

    for i, chapter in enumerate(chapters, start=1):
        file_name, xhtml_content = _build_chapter_xhtml(chapter, txt_body, i)

        chapter_item = epub.EpubHtml(
            title=chapter.chapter_title,
            file_name=file_name,
            lang="zh-TW",
        )
        chapter_item.content = xhtml_content.encode("utf-8")
        book.add_item(chapter_item)

        chapter_files.append((file_name, chapter_item))
        spine_items.append(chapter_item)
        toc_items.append(epub.Link(file_name, chapter.chapter_title, f"ch{i}"))

    nav_content = _build_nav_document(chapters, txt_body, title)
    nav_item = epub.EpubHtml(title="目錄", file_name="nav.xhtml", lang="zh-TW")
    nav_item.content = nav_content.encode("utf-8")
    book.add_item(nav_item)

    css_item = epub.EpubItem(
        uid="style_css",
        file_name="style.css",
        media_type="text/css",
        content=_build_css().encode("utf-8"),
    )
    book.add_item(css_item)

    book.spine = spine_items
    book.toc = tuple(toc_items)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    try:
        epub.write_epub(str(output_path), book)
    except OSError:
        # OSError covers: OSError, IOError, PermissionError, FileNotFoundError
        # EPUB write failure MUST NOT break Core Delivery
        return False  # graceful: I/O error

    return True