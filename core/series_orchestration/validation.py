"""P0 Stage 5 Batch 5.7 — Series Orchestration Validation.

Cross-series isolation enforcement and workflow validation.
"""

from __future__ import annotations

from typing import Any


class SeriesOrchestrationValidationError(Exception):
    """Raised when Series orchestration validation fails."""
    pass


class SeriesOrchestrationIsolationError(Exception):
    """Raised when cross-series isolation violation detected (fail-closed)."""
    def __init__(self, operation: str, expected_series_id: str, actual_series_id: str):
        super().__init__(
            f"Cross-series isolation violation in {operation}: "
            f"expected series_id={expected_series_id}, got series_id={actual_series_id}"
        )
        self.operation = operation
        self.expected_series_id = expected_series_id
        self.actual_series_id = actual_series_id


class SeriesWorkflowError(Exception):
    """Raised when workflow state transition is invalid."""
    pass


class SeriesBookNotFoundError(Exception):
    """Raised when book not found in series."""
    pass


def validate_series_operation(
    operation: str,
    expected_series_id: str,
    actual_series_id: str,
) -> None:
    """Validate series_id matches expected (fail-closed)."""
    if expected_series_id != actual_series_id:
        raise SeriesOrchestrationIsolationError(operation, expected_series_id, actual_series_id)


def validate_book_in_series(
    series_id: str,
    book_identity: str,
    series_manifest: Any,
) -> Any:  # SeriesBookEntry
    """Validate book belongs to series."""
    book = series_manifest.get_book_by_identity(book_identity)
    if book is None:
        raise SeriesBookNotFoundError(f"Book {book_identity} not in series {series_id}")
    return book


def validate_workflow_transition(
    current_status: str,
    new_status: str,
    operation: str,
) -> None:
    """Validate book workflow state transition."""
    valid_transitions = {
        "pending": {"in_progress", "failed", "archived"},
        "in_progress": {"completed", "failed", "archived"},
        "completed": {"promoted", "archived"},
        "promoted": {"archived"},
        "failed": {"archived"},
        "archived": set(),
    }
    if new_status not in valid_transitions.get(current_status, set()):
        raise SeriesWorkflowError(
            f"Invalid workflow transition in {operation}: {current_status} -> {new_status}"
        )


def validate_series_lifecycle_transition(
    current_status: str,
    new_status: str,
    operation: str,
) -> None:
    """Validate series lifecycle state transition."""
    valid_transitions = {
        "CREATED": {"ACTIVE", "ARCHIVED"},
        "ACTIVE": {"COMPLETED", "ARCHIVED"},
        "COMPLETED": {"ARCHIVED"},
        "ARCHIVED": set(),
    }
    if new_status not in valid_transitions.get(current_status, set()):
        raise SeriesWorkflowError(
            f"Invalid series lifecycle transition in {operation}: {current_status} -> {new_status}"
        )


def validate_promotion_approval_gate(approval_gate: bool, operation: str) -> None:
    """Validate promotion requires MANUAL approval gate (D-07 frozen)."""
    if approval_gate is False:
        raise SeriesOrchestrationValidationError(
            f"{operation} requires MANUAL approval gate (D-07 frozen). "
            "Auto-promotion is not permitted."
        )


def validate_concurrent_books(
    series_manifest: Any,
    operation: str,
) -> None:
    """Validate no concurrent books in progress (Stage 5: disallowed)."""
    in_progress = [b for b in series_manifest.books if b.status.value == "in_progress"]
    if len(in_progress) > 0:
        raise SeriesWorkflowError(
            f"{operation}: Concurrent books disallowed in Stage 5. "
            f"Book {in_progress[0].volume_number} is already in_progress."
        )


def validate_series_not_archived(
    series_manifest: Any,
    operation: str,
) -> None:
    """Validate series is not archived."""
    if series_manifest.lifecycle_status.value == "ARCHIVED":
        raise SeriesWorkflowError(
            f"{operation}: Cannot operate on archived series {series_manifest.series_id}"
        )


def validate_volume_number(
    series_manifest: Any,
    volume_number: int,
    operation: str,
) -> None:
    """Validate volume number is valid for series."""
    expected = series_manifest.next_volume_number()
    if volume_number != expected:
        raise SeriesOrchestrationValidationError(
            f"{operation}: Invalid volume_number: expected {expected}, got {volume_number}"
        )


def validate_book_status_for_promotion(
    book_status: str,
    operation: str,
) -> None:
    """Validate book status is 'completed' for promotion."""
    if book_status != "completed":
        raise SeriesWorkflowError(
            f"{operation}: Book must be 'completed' for promotion, current status: {book_status}"
        )


def validate_dry_run_safety(
    operation: str,
    *,
    mutates_state: bool = False,
    calls_provider: bool = False,
    performs_network: bool = False,
    executes_translation: bool = False,
) -> None:
    """Validate dry-run safety constraints."""
    if mutates_state:
        raise SeriesOrchestrationValidationError(
            f"Dry-run {operation} must not mutate state"
        )
    if calls_provider:
        raise SeriesOrchestrationValidationError(
            f"Dry-run {operation} must not call provider"
        )
    if performs_network:
        raise SeriesOrchestrationValidationError(
            f"Dry-run {operation} must not perform network access"
        )
    if executes_translation:
        raise SeriesOrchestrationValidationError(
            f"Dry-run {operation} must not execute translation"
        )