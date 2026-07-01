"""Foundation-08.9 Knowledge Maintenance public API."""

from .cleanup import KnowledgeCleanup
from .diagnostics import KnowledgeDiagnostics
from .integrity import KnowledgeIntegrityChecker, KnowledgeIntegrityReport, check_knowledge_integrity
from .manifest import build_knowledge_maintenance_manifest
from .manager import KnowledgeMaintenanceManager, build_knowledge_maintenance_manager
from .optimizer import KnowledgeOptimizer
from .repair import KnowledgeRepairEngine
from .statistics import KnowledgeStatistics, build_knowledge_statistics

__all__ = [
    "KnowledgeCleanup",
    "KnowledgeDiagnostics",
    "KnowledgeIntegrityChecker",
    "KnowledgeIntegrityReport",
    "KnowledgeMaintenanceManager",
    "KnowledgeOptimizer",
    "KnowledgeRepairEngine",
    "KnowledgeStatistics",
    "build_knowledge_maintenance_manager",
    "build_knowledge_maintenance_manifest",
    "build_knowledge_statistics",
    "check_knowledge_integrity",
]
