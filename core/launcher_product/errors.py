class LauncherProductError(Exception):
    """Base error for launcher product operations."""


class LauncherConfigError(LauncherProductError):
    """Raised when a launcher configuration cannot be loaded."""


class InputInspectionError(LauncherProductError):
    """Raised when an input file cannot be inspected safely."""
