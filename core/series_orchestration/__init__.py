"""P0 Stage 5 Batch 5.7 — Series Orchestration.

High-level orchestration for multi-book series translation workflows.
"""

from __future__ import annotations

from .coordinator import SeriesTranslationCoordinator
from .workflow import (
    BookWorkflowState,
    SeriesWorkflowState,
    SeriesCreateResult,
    BookAddResult,
    TranslationReport,
    PromotionReport,
    SeriesStatusReport,
)
from .runtime_integration import SeriesContext, build_series_context, inject_series_context
from .cli_integration import (
    cmd_series_create,
    cmd_series_list,
    cmd_series_status,
    cmd_series_rename,
    cmd_series_add_book,
    cmd_series_promote_book,
    cmd_translate_with_series,
    cmd_series_resume,
)
from .validation import (
    SeriesOrchestrationValidationError,
    SeriesOrchestrationIsolationError,
    SeriesWorkflowError,
    SeriesBookNotFoundError,
    validate_series_operation,
    validate_book_in_series,
    validate_workflow_transition,
    validate_series_lifecycle_transition,
    validate_promotion_approval_gate,
    validate_concurrent_books,
    validate_series_not_archived,
    validate_volume_number,
    validate_book_status_for_promotion,
    validate_dry_run_safety,
)

__all__ = [
    "SeriesTranslationCoordinator",
    "BookWorkflowState",
    "SeriesWorkflowState",
    "SeriesCreateResult",
    "BookAddResult",
    "TranslationReport",
    "PromotionReport",
    "SeriesStatusReport",
    "SeriesContext",
    "build_series_context",
    "inject_series_context",
    "cmd_series_create",
    "cmd_series_list",
    "cmd_series_status",
    "cmd_series_rename",
    "cmd_series_add_book",
    "cmd_series_promote_book",
    "cmd_translate_with_series",
    "cmd_series_resume",
    "SeriesOrchestrationValidationError",
    "SeriesOrchestrationIsolationError",
    "SeriesWorkflowError",
    "SeriesBookNotFoundError",
    "validate_series_operation",
    "validate_book_in_series",
    "validate_workflow_transition",
    "validate_series_lifecycle_transition",
    "validate_promotion_approval_gate",
    "validate_concurrent_books",
    "validate_series_not_archived",
    "validate_volume_number",
    "validate_book_status_for_promotion",
    "validate_dry_run_safety",
]

version = "p0-stage5-batch5.7"