"""RM-7.0 Knowledge Evolution Foundation — public API.

Completely offline knowledge lifecycle management:
  - models:   frozen dataclasses for entities, aliases, conflicts, reports
  - store:    JSON file-based tiered persistence
  - resolver: priority-chain lookup (USER > RUNTIME > LEARNING > AUTO)
  - manager:  CRUD operations + alias/candidate lifecycle
  - evolution: offline learning engine for term discovery
  - serializer: JSON / Markdown / Report output

No provider imports. No network. No translation engine dependencies.
"""

from .evolution import KnowledgeEvolution
from .manager import KnowledgeManager
from .models import (
    AliasEntry,
    CandidateStatus,
    ConflictRecord,
    EntityType,
    EvolutionReport,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
    PRIORITY_ORDER,
    Severity,
)
from .resolver import KnowledgeResolver
from .serializer import (
    KnowledgeSerializer,
    aliases_to_markdown,
    entities_to_markdown,
    report_to_markdown,
    to_json,
)
from .store import KnowledgeStore

__all__ = [
    "KnowledgeStore",
    "KnowledgeResolver",
    "KnowledgeManager",
    "KnowledgeEvolution",
    "KnowledgeSerializer",
    "KnowledgeEntity",
    "AliasEntry",
    "ConflictRecord",
    "EvolutionReport",
    "LearningCandidate",
    "EntityType",
    "PriorityLevel",
    "PRIORITY_ORDER",
    "Severity",
    "CandidateStatus",
    "to_json",
    "entities_to_markdown",
    "aliases_to_markdown",
    "report_to_markdown",
]