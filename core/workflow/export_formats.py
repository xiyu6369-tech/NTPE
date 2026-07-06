# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

import html
import json
from pathlib import Path
from typing import Optional

from .export_context import ExportContext
from .export_result import ExportResult
from .export_template import ExportTemplate


class BaseExporter:
    format = "base"
    extension = "txt"

    def render(self, context: ExportContext) -> str:
        return context.content

    def export(self, context: ExportContext) -> ExportResult:
        content = self.render(context)
        path = context.resolved_path(self.extension)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return ExportResult(
            format=self.format,
            success=True,
            content=content,
            path=str(path) if path else None,
            metadata=context.metadata.to_dict(),
        )


class TxtExporter(BaseExporter):
    format = "txt"
    extension = "txt"

    def render(self, context: ExportContext) -> str:
        template: Optional[ExportTemplate] = context.options.get("template")
        return template.render(context.content) if template else context.content


class MarkdownExporter(BaseExporter):
    format = "markdown"
    extension = "md"

    def render(self, context: ExportContext) -> str:
        title = context.metadata.title or "Untitled"
        return f"# {title}\n\n{context.content.strip()}\n"


class HtmlExporter(BaseExporter):
    format = "html"
    extension = "html"

    def render(self, context: ExportContext) -> str:
        title = html.escape(context.metadata.title or "Untitled")
        body = "\n".join(f"<p>{html.escape(p)}</p>" for p in context.content.split("\n") if p.strip())
        return f"<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>{title}</title></head><body>{body}</body></html>"


class DocxExporter(BaseExporter):
    format = "docx"
    extension = "docx"

    def render(self, context: ExportContext) -> str:
        # Dependency-free placeholder payload for the framework layer.
        # A real DOCX writer can be plugged in without changing the public API.
        return json.dumps({"format": "docx", "metadata": context.metadata.to_dict(), "content": context.content}, ensure_ascii=False, indent=2)


class EpubExporter(BaseExporter):
    format = "epub"
    extension = "epub"

    def render(self, context: ExportContext) -> str:
        return json.dumps({"format": "epub", "metadata": context.metadata.to_dict(), "content": context.content}, ensure_ascii=False, indent=2)


class PdfExporter(BaseExporter):
    format = "pdf"
    extension = "pdf"

    def render(self, context: ExportContext) -> str:
        return json.dumps({"format": "pdf", "metadata": context.metadata.to_dict(), "content": context.content}, ensure_ascii=False, indent=2)
