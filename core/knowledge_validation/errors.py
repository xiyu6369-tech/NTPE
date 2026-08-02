"""
Knowledge Validation Error Definitions
RM-5.7.3A Schema Validation Engine

Exception hierarchy for schema validation errors.
"""

from core.exceptions import ValidationError as BaseValidationError


class ValidationError(BaseValidationError):
    """Base exception for knowledge validation errors."""
    pass


class SchemaNotFoundError(ValidationError):
    """Raised when a requested schema cannot be found."""

    def __init__(self, schema_name: str, searched_paths: list[str] | None = None):
        self.schema_name = schema_name
        self.searched_paths = searched_paths or []
        msg = f"Schema '{schema_name}' not found"
        if self.searched_paths:
            msg += f" (searched: {', '.join(self.searched_paths)})"
        super().__init__(msg)


class SchemaVersionMismatchError(ValidationError):
    """Raised when schema_version in data doesn't match expected version."""

    def __init__(
        self,
        schema_name: str,
        expected_version: str,
        actual_version: str | None,
    ):
        self.schema_name = schema_name
        self.expected_version = expected_version
        self.actual_version = actual_version
        msg = (
            f"Schema version mismatch for '{schema_name}': "
            f"expected '{expected_version}', got '{actual_version}'"
        )
        super().__init__(msg)


class ValidationFailedError(ValidationError):
    """Raised when validation fails with collected errors."""

    def __init__(self, schema_name: str, errors: list[dict]):
        self.schema_name = schema_name
        self.errors = errors
        error_count = len(errors)
        msg = f"Validation failed for '{schema_name}' with {error_count} error(s)"
        super().__init__(msg)


class SchemaLoadError(ValidationError):
    """Raised when schema file cannot be loaded or parsed."""

    def __init__(self, schema_path: str, cause: Exception | None = None):
        self.schema_path = schema_path
        self.cause = cause
        msg = f"Failed to load schema from '{schema_path}'"
        if cause:
            msg += f": {cause}"
        super().__init__(msg)


class UnsupportedSchemaDraftError(ValidationError):
    """Raised when schema uses unsupported JSON Schema draft."""

    def __init__(self, schema_name: str, draft: str):
        self.schema_name = schema_name
        self.draft = draft
        msg = f"Unsupported JSON Schema draft '{draft}' in schema '{schema_name}'"
        super().__init__(msg)