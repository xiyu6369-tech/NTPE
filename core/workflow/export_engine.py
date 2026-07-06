# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from .export_context import ExportContext
from .export_events import EXPORT_COMPLETED, EXPORT_FAILED, EXPORT_STARTED, ExportEvent, ExportEventBus
from .export_formats import DocxExporter, EpubExporter, HtmlExporter, MarkdownExporter, PdfExporter, TxtExporter
from .export_registry import ExportRegistry
from .export_result import ExportResult
from .export_validator import ExportValidator


class ExportEngine:
    def __init__(self) -> None:
        self.registry = ExportRegistry()
        self.events = ExportEventBus()
        self.validator = ExportValidator()
        self.results = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        for exporter in (TxtExporter(), MarkdownExporter(), HtmlExporter(), DocxExporter(), EpubExporter(), PdfExporter()):
            self.registry.register(exporter)

    def export(self, context: ExportContext) -> ExportResult:
        self.validator.validate_context(context)
        export_format = context.format.lower()
        self.events.emit(ExportEvent(EXPORT_STARTED, export_format, {"metadata": context.metadata.to_dict()}))
        try:
            exporter = self.registry.get(export_format)
            result = exporter.export(context)
            self.validator.validate_result(result)
            self.results.append(result)
            self.events.emit(ExportEvent(EXPORT_COMPLETED, export_format, result.to_dict()))
            return result
        except Exception as exc:
            result = ExportResult(format=export_format, success=False, error=str(exc))
            self.results.append(result)
            self.events.emit(ExportEvent(EXPORT_FAILED, export_format, result.to_dict()))
            return result
