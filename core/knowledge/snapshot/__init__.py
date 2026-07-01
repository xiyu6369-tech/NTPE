"""Foundation-08.7 Knowledge Snapshot Manager public API."""

from .manifest import build_knowledge_snapshot_manifest
from .snapshot_diff import KnowledgeSnapshotDiff, KnowledgeSnapshotDiffer, merge_snapshots
from .snapshot_history import KnowledgeSnapshotHistory, KnowledgeSnapshotHistoryEntry
from .snapshot_manager import KnowledgeSnapshotManager, build_snapshot_manager
from .snapshot_registry import KnowledgeSnapshotRegistry
from .snapshot_serializer import KnowledgeSnapshotSerializer

__all__ = [
    "KnowledgeSnapshotDiff",
    "KnowledgeSnapshotDiffer",
    "KnowledgeSnapshotHistory",
    "KnowledgeSnapshotHistoryEntry",
    "KnowledgeSnapshotManager",
    "KnowledgeSnapshotRegistry",
    "KnowledgeSnapshotSerializer",
    "build_knowledge_snapshot_manifest",
    "build_snapshot_manager",
    "merge_snapshots",
]
