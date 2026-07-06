# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from .export_context import ExportContext
from .export_exceptions import ExportValidationError
from .export_result import ExportResult


class ExportValidator:
    def validate_context(self, context: ExportContext) -> None:
        if context is None:
            raise ExportValidationError("export_context_required")
        if not isinstance(context.content, str):
            raise ExportValidationError("export_content_must_be_string")
        if not context.format:
            raise ExportValidationError("export_format_required")

    def validate_result(self, result: ExportResult) -> None:
        if result.success and result.content is None and not result.path:
            raise ExportValidationError("export_result_missing_content_or_path")
