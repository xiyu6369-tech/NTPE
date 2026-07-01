"""Foundation-08.9 Knowledge diagnostics."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..repositories.manager import KnowledgeRepositoryManager
from .integrity import KnowledgeIntegrityChecker
from .statistics import KnowledgeStatistics
from .manifest import build_knowledge_maintenance_manifest


class KnowledgeDiagnostics:
    """Generate health and diagnostics reports for the Knowledge Layer."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()
        self.integrity = KnowledgeIntegrityChecker(self.repository_manager)
        self.statistics = KnowledgeStatistics(self.repository_manager)

    def health_report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        integrity = self.integrity.check().to_dict()
        stats = self.statistics.report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)
        return {
            "version": self.version,
            "healthy": bool(integrity.get("valid")),
            "integrity": integrity,
            "statistics": stats,
            "manifest": build_knowledge_maintenance_manifest(),
        }

    def diagnostics_report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        report = self.health_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)
        report["diagnostics"] = {
            "repository_available": self.repository_manager.repository is not None,
            "cache_available": cache_manager is not None,
            "snapshot_available": snapshot_manager is not None,
        }
        return report


__all__ = ["KnowledgeDiagnostics"]
