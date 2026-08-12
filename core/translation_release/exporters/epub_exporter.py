from __future__ import annotations

from pathlib import Path
from typing import Any

from core.translation_release.exporters.base import BaseExporter
from core.translation_release.models import DeliveryManifest, TOCEntry
from core.translation_release.reader_structure.epub_packager import pack_epub
from core.translation_release.reader_structure.models import ReaderChapterMap


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
        reader_chapter_map: ReaderChapterMap | None = None,
        translated_chunks: list[str] | None = None,
        chunk_records: list[dict] | None = None,
    ) -> bool:
        """
        EPUB 3.0 generation using Phase 1 ReaderChapterMap (preferred) or fallback.

        Priority:
        1. If reader_chapter_map is provided: use pack_epub with proper chapter slicing
        2. If translated_chunks and chunk_records provided: build ReaderChapterMap then use pack_epub
        3. Fallback: single-chapter EPUB (legacy behavior, for backward compatibility only)
        """
        # Try to use the new packager with proper chapter mapping
        if reader_chapter_map is not None:
            return self._export_with_chapter_map(polished_text, manifest, output_path, reader_chapter_map)

        if translated_chunks is not None and chunk_records is not None:
            return self._export_with_chapter_data(polished_text, manifest, output_path, translated_chunks, chunk_records)

        # Legacy fallback: single chapter
        return self._export_legacy_single_chapter(polished_text, manifest, output_path)

    def _export_with_chapter_map(
        self,
        polished_text: str,
        manifest: DeliveryManifest,
        output_path: Path,
        reader_chapter_map: ReaderChapterMap,
    ) -> bool:
        """Export using pre-built ReaderChapterMap."""
        try:
            meta = {
                "title": manifest.novel_id,
                "author": manifest.artifacts.get("author", "未知作者") if isinstance(manifest.artifacts, dict) else "未知作者",
                "translator": "NTPE Translation Engine",
                "date": manifest.generated_at,
                "pipeline_version": manifest.pipeline_version,
            }
            return pack_epub(
                txt_body=polished_text,
                reader_chapter_map=reader_chapter_map,
                novel_id=manifest.novel_id,
                output_path=output_path,
                metadata=meta,
            )
        except (ImportError, AttributeError, ValueError, OSError):
            # OSError covers: OSError, IOError, PermissionError, FileNotFoundError
            return False

    def _export_with_chapter_data(
        self,
        polished_text: str,
        manifest: DeliveryManifest,
        output_path: Path,
        translated_chunks: list[str],
        chunk_records: list[dict],
    ) -> bool:
        """Build ReaderChapterMap from chunk data and export."""
        try:
            from core.translation_release.reader_structure.chapter_mapper import build_reader_chapter_map
            reader_chapter_map = build_reader_chapter_map(
                txt_body=polished_text,
                translated_chunks=translated_chunks,
                chunk_records=chunk_records,
            )
            return self._export_with_chapter_map(polished_text, manifest, output_path, reader_chapter_map)
        except (ImportError, AttributeError, ValueError, OSError):
            # OSError covers: OSError, IOError, PermissionError, FileNotFoundError
            return False

    def _export_legacy_single_chapter(
        self,
        polished_text: str,
        manifest: DeliveryManifest,
        output_path: Path,
    ) -> bool:
        """Legacy single-chapter EPUB export (backward compatibility)."""
        try:
            from ebooklib import epub
        except ImportError:
            return False

        book = epub.EpubBook()
        book.set_identifier(manifest.novel_id)
        title = manifest.table_of_contents[0]["title"] if manifest.table_of_contents else manifest.novel_id
        book.set_title(title)
        book.set_language("zh-TW")
        book.add_author(manifest.artifacts.get("author", "未知作者") if isinstance(manifest.artifacts, dict) else "未知作者")

        book.add_metadata("DC", "translator", "NTPE Translation Engine")
        book.add_metadata("DC", "date", manifest.generated_at)
        book.add_metadata("DC", "pipeline", manifest.pipeline_version)

        chapter = epub.EpubHtml(title=title, file_name="chapter_1.xhtml", lang="zh-TW")
        content = polished_text.replace("\n", "<br/>\n")
        chapter.content = f"<html><body>{content}</body></html>"
        book.add_item(chapter)

        book.spine = ["nav", chapter]
        book.toc = (epub.Link("chapter_1.xhtml", title, "ch1"),)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(str(output_path), book)
        return True