# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from typing import Dict, Iterable

from .export_exceptions import ExporterNotFoundError


class ExportRegistry:
    def __init__(self) -> None:
        self._exporters: Dict[str, object] = {}

    def register(self, exporter: object) -> object:
        export_format = getattr(exporter, "format", "").lower()
        if not export_format:
            raise ValueError("exporter_format_required")
        self._exporters[export_format] = exporter
        return exporter

    def get(self, export_format: str) -> object:
        key = export_format.lower()
        if key not in self._exporters:
            raise ExporterNotFoundError(f"exporter_not_found:{export_format}")
        return self._exporters[key]

    def formats(self) -> Iterable[str]:
        return tuple(sorted(self._exporters.keys()))
