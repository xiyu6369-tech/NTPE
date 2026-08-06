"""RM-6.1.0 Knowledge Runtime error types."""

from __future__ import annotations


class KnowledgeRuntimeError(Exception):
    """Base error for Knowledge Runtime operations."""


class KnowledgeLoadError(KnowledgeRuntimeError):
    """Raised when a knowledge base cannot be loaded."""


class KnowledgeResolveError(KnowledgeRuntimeError):
    """Raised when an entry cannot be resolved."""


class KnowledgeSnapshotError(KnowledgeRuntimeError):
    """Raised when snapshot serialization or restoration fails."""


class KnowledgeManagerError(KnowledgeRuntimeError):
    """Raised when manager orchestration fails."""


__all__ = [
    "KnowledgeRuntimeError",
    "KnowledgeLoadError",
    "KnowledgeResolveError",
    "KnowledgeSnapshotError",
    "KnowledgeManagerError",
]