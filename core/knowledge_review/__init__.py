"""
Knowledge Review Workflow Module

提供知識審核工作流的核心功能，包含：
- 狀態管理
- 審核項目模型
- 信心度閘控
- 審核隊列
- 審核引擎
- 審計日誌
"""

from .states import (
    ReviewState,
    STATE_TRANSITIONS,
    InvalidStateTransition,
    validate_transition,
    get_valid_transitions,
)
from .models import ReviewItem, EntityType, ValidationResult
from .confidence_gate import ConfidenceGate, ConfidenceGateResult, ConfidenceGateDecision
from .review_queue import ReviewQueue, Priority
from .review_engine import ReviewEngine, ReviewAction, ReviewDecision
from .audit_log import ReviewAuditEntry, AuditLog
from .errors import (
    KnowledgeReviewError,
    InvalidReviewStateError,
    ReviewItemNotFoundError,
    DuplicateReviewItemError,
    InvalidConfidenceScoreError,
)

__all__ = [
    # States
    "ReviewState",
    "STATE_TRANSITIONS",
    "InvalidStateTransition",
    "validate_transition",
    "get_valid_transitions",
    # Models
    "ReviewItem",
    "EntityType",
    "ValidationResult",
    # Confidence Gate
    "ConfidenceGate",
    "ConfidenceGateResult",
    "ConfidenceGateDecision",
    # Review Queue
    "ReviewQueue",
    "Priority",
    # Review Engine
    "ReviewEngine",
    "ReviewAction",
    "ReviewDecision",
    # Audit Log
    "ReviewAuditEntry",
    "AuditLog",
    # Errors
    "KnowledgeReviewError",
    "InvalidReviewStateError",
    "ReviewItemNotFoundError",
    "DuplicateReviewItemError",
    "InvalidConfidenceScoreError",
]

__version__ = "1.0.0"