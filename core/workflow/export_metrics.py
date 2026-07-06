# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from typing import Iterable, Dict, Any

from .export_result import ExportResult


def build_export_metrics(results: Iterable[ExportResult]) -> Dict[str, Any]:
    items = list(results)
    success = sum(1 for item in items if item.success)
    failed = len(items) - success
    return {
        "total": len(items),
        "success": success,
        "failed": failed,
        "formats": sorted({item.format for item in items}),
    }
