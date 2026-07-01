"""Foundation-08.9 Knowledge Maintenance Manager."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..repositories.manager import KnowledgeRepositoryManager
from .cleanup import KnowledgeCleanup
from .diagnostics import KnowledgeDiagnostics
from .integrity import KnowledgeIntegrityChecker
from .manifest import build_knowledge_maintenance_manifest
from .optimizer import KnowledgeOptimizer
from .repair import KnowledgeRepairEngine
from .statistics import KnowledgeStatistics


class KnowledgeMaintenanceManager:
    """Unified facade for cleanup, integrity, repair, optimization, and reports."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None, event_bus: Any = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()
        self.event_bus = event_bus
        self.cleanup = KnowledgeCleanup(self.repository_manager)
        self.optimizer = KnowledgeOptimizer(self.repository_manager)
        self.integrity = KnowledgeIntegrityChecker(self.repository_manager)
        self.repair = KnowledgeRepairEngine(self.repository_manager)
        self.statistics = KnowledgeStatistics(self.repository_manager)
        self.diagnostics = KnowledgeDiagnostics(self.repository_manager)

    def _publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.event_bus is None:
            return
        data = {"version": self.version, **dict(payload or {})}
        try:
            self.event_bus.publish(event_type, data)
        except TypeError:
            try:
                self.event_bus.publish({"event_type": event_type, "payload": data})
            except Exception:
                pass
        except Exception:
            pass

    def repository_cleanup(self) -> Dict[str, Any]:
        result = self.cleanup.repository_cleanup()
        self._publish("KnowledgeMaintenanceRepositoryCleanup", result)
        return result

    def repository_optimize(self) -> Dict[str, Any]:
        result = self.optimizer.repository_optimize()
        self._publish("KnowledgeMaintenanceRepositoryOptimized", result)
        return result

    def repository_rebuild(self, snapshot: Any = None) -> Dict[str, Any]:
        result = self.optimizer.repository_rebuild(snapshot)
        self._publish("KnowledgeMaintenanceRepositoryRebuilt", result)
        return result

    def cache_cleanup(self, cache_manager: Any = None) -> Dict[str, Any]:
        result = self.cleanup.cache_cleanup(cache_manager)
        self._publish("KnowledgeMaintenanceCacheCleanup", result)
        return result

    def cache_rebuild(self, cache_manager: Any = None) -> Dict[str, Any]:
        result = self.optimizer.cache_rebuild(cache_manager)
        self._publish("KnowledgeMaintenanceCacheRebuilt", result)
        return result

    def snapshot_cleanup(self, snapshot_manager: Any = None, keep_latest: int = 1) -> Dict[str, Any]:
        result = self.cleanup.snapshot_cleanup(snapshot_manager, keep_latest=keep_latest)
        self._publish("KnowledgeMaintenanceSnapshotCleanup", result)
        return result

    def snapshot_compact(self, snapshot_manager: Any = None, keep_latest: int = 5) -> Dict[str, Any]:
        result = self.optimizer.snapshot_compact(snapshot_manager, keep_latest=keep_latest)
        self._publish("KnowledgeMaintenanceSnapshotCompacted", result)
        return result

    def integrity_check(self) -> Dict[str, Any]:
        result = self.integrity.check().to_dict()
        self._publish("KnowledgeMaintenanceIntegrityChecked", result)
        return result

    def repair_engine(self) -> KnowledgeRepairEngine:
        return self.repair

    def auto_repair(self) -> Dict[str, Any]:
        result = self.repair.auto_repair()
        self._publish("KnowledgeMaintenanceRepaired", result)
        return result

    def duplicate_detection(self) -> Dict[str, Any]:
        duplicates = self.repair.detect_duplicates()
        return {"version": self.version, "duplicate_count": len(duplicates), "duplicates": duplicates}

    def statistics_report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        return self.statistics.report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)

    def diagnostics_report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        return self.diagnostics.diagnostics_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)

    def health_report(self, cache_manager: Any = None, snapshot_manager: Any = None) -> Dict[str, Any]:
        return self.diagnostics.health_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)

    def manifest(self) -> Dict[str, Any]:
        return build_knowledge_maintenance_manifest({"repository": self.repository_manager.repository.manifest().to_dict()})

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


def build_knowledge_maintenance_manager(repository_manager: Optional[KnowledgeRepositoryManager] = None, **_: Any) -> KnowledgeMaintenanceManager:
    return KnowledgeMaintenanceManager(repository_manager=repository_manager)


__all__ = ["KnowledgeMaintenanceManager", "build_knowledge_maintenance_manager"]
