"""RM-6.1.2 Knowledge Runtime Foundation public API."""

from .errors import (
    KnowledgeLoadError,
    KnowledgeManagerError,
    KnowledgeResolveError,
    KnowledgeRuntimeError,
    KnowledgeSnapshotError,
)
from .loader import KnowledgeLoader
from .manager import KnowledgeRuntimeManager
from .merger import (
    DOMAIN_STRATEGIES,
    KnowledgeMerger,
    MergeStrategy,
    MergedKnowledge,
    MergedRuntime,
)
from .models import (
    KnowledgeBundle,
    KnowledgeDomain,
    KnowledgeEntry,
    KnowledgePrototype,
    KnowledgeSnapshot,
)
from .resolver import KnowledgeResolver
from .snapshot import KnowledgeSnapshotStore, SnapshotHierarchy

__all__ = [
    "KnowledgeRuntimeError",
    "KnowledgeLoadError",
    "KnowledgeManagerError",
    "KnowledgeResolveError",
    "KnowledgeSnapshotError",
    "KnowledgeEntry",
    "KnowledgePrototype",
    "KnowledgeBundle",
    "KnowledgeDomain",
    "KnowledgeSnapshot",
    "KnowledgeSnapshotStore",
    "SnapshotHierarchy",
    "KnowledgeLoader",
    "KnowledgeResolver",
    "KnowledgeRuntimeManager",
    "MergeStrategy",
    "DOMAIN_STRATEGIES",
    "MergedKnowledge",
    "MergedRuntime",
    "KnowledgeMerger",
]