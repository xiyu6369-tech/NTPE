# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================


class ExportError(Exception):
    """Base export framework error."""


class ExporterNotFoundError(ExportError):
    """Raised when an export format is not registered."""


class ExportValidationError(ExportError):
    """Raised when export input or output validation fails."""
