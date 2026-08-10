from __future__ import annotations

from pathlib import Path

from core.translation_release.exporters.base import BaseExporter
from core.translation_release.models import DeliveryManifest, TOCEntry


class EpubExporter(BaseExporter):
    format_name = "epub"
    file_extension = ".epub"

    def export(
        self,
        *,
        polished_text: str,
        manifest: DeliveryManifest,
        toc: list[TOCEntry],
        output_path: Path,
    ) -> bool:
        """
        Minimal EPUB 3.0 generation:
        - Uses polished_text as single chapter or splits by TOC
        - Embeds metadata from manifest
        - Includes TOC navigation
        - No CSS styling beyond basic readability
        - Dependencies: ebooklib (optional, graceful fallback)
        """
        try:
            from ebooklib import epub
        except ImportError:
            return False  # graceful: format unavailable

        book = epub.EpubBook()
        book.set_identifier(manifest.novel_id)
        title = manifest.table_of_contents[0]["title"] if manifest.table_of_contents else manifest.novel_id
        book.set_title(title)
        book.set_language("zh-TW")
        book.add_author(manifest.artifacts.get("author", "未知作者") if isinstance(manifest.artifacts, dict) else "未知作者")

        # Add metadata
        book.add_metadata("DC", "translator", "NTPE Translation Engine")
        book.add_metadata("DC", "date", manifest.generated_at)
        book.add_metadata("DC", "pipeline", manifest.pipeline_version)

        # Create a single chapter from polished_text
        chapter = epub.EpubHtml(title=title, file_name="chapter_1.xhtml", lang="zh-TW")
        # Simple HTML wrapping
        content = polished_text.replace("\n", "<br/>\n")
        chapter.content = f"<html><body>{content}</body></html>"
        book.add_item(chapter)

        # Add to spine and TOC
        book.spine = ["nav", chapter]
        book.toc = (epub.Link("chapter_1.xhtml", title, "ch1"),)

        # Add navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(str(output_path), book)
        return True