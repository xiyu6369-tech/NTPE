# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from typing import Iterable, List

from .export_context import ExportContext
from .export_result import ExportResult


class ExportPipeline:
    def __init__(self, engine: object) -> None:
        self.engine = engine

    def export_many(self, content: str, formats: Iterable[str], **kwargs) -> List[ExportResult]:
        results: List[ExportResult] = []
        for export_format in formats:
            context = ExportContext(content=content, format=export_format, **kwargs)
            results.append(self.engine.export(context))
        return results
