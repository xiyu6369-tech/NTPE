"""
Validation Result Data Structures
RM-5.7.3A Schema Validation Engine

Normalized validation output for consistent error reporting.
"""

from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime


@dataclass
class ValidationErrorDetail:
    """Normalized validation error detail."""

    keyword: str
    """JSON Schema validation keyword that failed (e.g., 'type', 'required', 'enum')"""

    instance_path: str
    """JSON Pointer path to the failing instance location"""

    schema_path: str
    """JSON Pointer path to the failing schema location"""

    message: str
    """Human-readable error message"""

    expected: Any | None = None
    """Expected value/type (when applicable)"""

    actual: Any | None = None
    """Actual value that caused the error (when applicable)"""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "keyword": self.keyword,
            "instance_path": self.instance_path,
            "schema_path": self.schema_path,
            "message": self.message,
        }
        if self.expected is not None:
            result["expected"] = self.expected
        if self.actual is not None:
            result["actual"] = self.actual
        return result


@dataclass
class ValidationResult:
    """
    Normalized validation result.

    Output format:
    {
        "valid": true,
        "schema": "character_schema",
        "errors": []
    }
    """

    valid: bool
    """Whether validation passed"""

    schema: str
    """Name/identifier of the schema used for validation"""

    errors: list[ValidationErrorDetail] = field(default_factory=list)
    """List of validation errors (empty if valid)"""

    schema_version: str | None = None
    """Schema version that was validated against"""

    instance_version: str | None = None
    """Schema version found in the instance data (if any)"""

    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    """UTC timestamp of validation"""

    metadata: dict = field(default_factory=dict)
    """Additional metadata (validation duration, etc.)"""

    @property
    def error_count(self) -> int:
        """Number of validation errors."""
        return len(self.errors)

    @property
    def has_errors(self) -> bool:
        """Whether there are any validation errors."""
        return len(self.errors) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary matching the specified output format."""
        return {
            "valid": self.valid,
            "schema": self.schema,
            "errors": [e.to_dict() for e in self.errors],
        }

    def to_dict_full(self) -> dict:
        """Convert to full dictionary with all fields."""
        return {
            "valid": self.valid,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "instance_version": self.instance_version,
            "validated_at": self.validated_at,
            "error_count": self.error_count,
            "errors": [e.to_dict() for e in self.errors],
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        schema: str,
        schema_version: str | None = None,
        instance_version: str | None = None,
        **metadata,
    ) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            valid=True,
            schema=schema,
            schema_version=schema_version,
            instance_version=instance_version,
            **metadata,
        )

    @classmethod
    def failure(
        cls,
        schema: str,
        errors: list[ValidationErrorDetail],
        schema_version: str | None = None,
        instance_version: str | None = None,
        **metadata,
    ) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(
            valid=False,
            schema=schema,
            errors=errors,
            schema_version=schema_version,
            instance_version=instance_version,
            **metadata,
        )