"""
Benchmark Error Definitions (RM-5.8.2)

All benchmark-specific exceptions.
"""

from __future__ import annotations

from typing import Any, Optional


class BenchmarkError(Exception):
    """Base exception for all benchmark errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class GoldenDatasetError(BenchmarkError):
    """Errors related to golden dataset loading/validation."""

    def __init__(
        self,
        message: str,
        dataset_path: Optional[str] = None,
        entry_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.dataset_path = dataset_path
        self.entry_id = entry_id


class ComparisonError(BenchmarkError):
    """Errors during golden vs prediction comparison."""

    def __init__(
        self,
        message: str,
        extractor_type: Optional[str] = None,
        golden_id: Optional[str] = None,
        prediction_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.extractor_type = extractor_type
        self.golden_id = golden_id
        self.prediction_id = prediction_id


class MetricComputationError(BenchmarkError):
    """Errors during metric computation."""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        extractor_type: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.metric_name = metric_name
        self.extractor_type = extractor_type


class InvalidInputError(BenchmarkError):
    """Errors for invalid input data."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Any = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value


class SchemaComplianceError(BenchmarkError):
    """Errors for schema validation failures."""

    def __init__(
        self,
        message: str,
        entity_id: Optional[str] = None,
        field_path: Optional[str] = None,
        expected_schema: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.entity_id = entity_id
        self.field_path = field_path
        self.expected_schema = expected_schema


class DeterminismError(BenchmarkError):
    """Errors when deterministic behavior is violated."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        input_hash: Optional[str] = None,
        output_hash_1: Optional[str] = None,
        output_hash_2: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.operation = operation
        self.input_hash = input_hash
        self.output_hash_1 = output_hash_1
        self.output_hash_2 = output_hash_2