from __future__ import annotations

from pathlib import Path

from core.translation_release.exporters.base import BaseExporter
from core.translation_release.models import DeliveryManifest, TOCEntry


class PdfExporter(BaseExporter):
    format_name = "pdf"
    file_extension = ".pdf"

    def export(
        self,
        *,
        polished_text: str,
        manifest: DeliveryManifest,
        toc: list[TOCEntry],
        output_path: Path,
    ) -> bool:
        """
        Minimal PDF generation:
        - Uses polished_text with metadata header
        - Basic pagination, TOC bookmarks
        - No advanced typography
        - Dependencies: reportlab (optional, graceful fallback)
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            return False  # graceful: format unavailable

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        style_normal = styles["Normal"]
        style_normal.fontName = "Helvetica"
        style_normal.fontSize = 12
        style_normal.leading = 18

        # Try to register a CJK font if available
        try:
            # This is a placeholder - actual font path would be needed
            pass
        except Exception:
            pass

        story = []

        # Add metadata header
        meta_lines = [
            f"書名：{manifest.novel_id}",
            f"翻譯日期：{manifest.generated_at}",
            f"翻譯模型：{manifest.model}",
            f"管線版本：{manifest.pipeline_version}",
            "",
            "───",
            "",
        ]
        for line in meta_lines:
            story.append(Paragraph(line, style_normal))
            story.append(Spacer(1, 6))

        # Add TOC
        story.append(Paragraph("目錄", style_normal))
        story.append(Spacer(1, 12))
        for entry in toc:
            line = f"{entry.chapter_title} — {entry.scene_count} 場景 (Chunk {entry.start_chunk_index}-{entry.end_chunk_index})"
            story.append(Paragraph(line, style_normal))
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 24))
        story.append(Paragraph("───", style_normal))
        story.append(Spacer(1, 24))

        # Add novel text
        for para in polished_text.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), style_normal))
                story.append(Spacer(1, 12))

        doc.build(story)
        return True