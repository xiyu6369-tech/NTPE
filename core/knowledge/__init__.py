"""Foundation-08.0 Knowledge Layer public API."""

from .contracts import (
    KnowledgeItem,
    KnowledgeManifest,
    KnowledgeProvider,
    KnowledgeQuery,
    KnowledgeRegistryContract,
    KnowledgeRepository,
    KnowledgeSnapshot,
)
from .manifest import build_knowledge_manifest
from .provider import RepositoryKnowledgeProvider
from .query import build_query
from .registry import KnowledgeRegistry, get_default_knowledge_registry
from .repository import InMemoryKnowledgeRepository, build_repository_from_intelligence_snapshot

__all__ = [
    "KnowledgeItem",
    "KnowledgeManifest",
    "KnowledgeProvider",
    "KnowledgeQuery",
    "KnowledgeRegistryContract",
    "KnowledgeRepository",
    "KnowledgeSnapshot",
    "InMemoryKnowledgeRepository",
    "RepositoryKnowledgeProvider",
    "KnowledgeRegistry",
    "build_query",
    "build_knowledge_manifest",
    "build_repository_from_intelligence_snapshot",
    "get_default_knowledge_registry",
]

# Foundation-08.1 Repository implementation exports
from .repositories import KnowledgeMemoryRepository, KnowledgeRepositoryManager, build_memory_repository
from .providers import (
    CharacterKnowledgeProvider,
    GlossaryKnowledgeProvider,
    NarrativeKnowledgeProvider,
    RuntimeKnowledgeProvider,
    SceneKnowledgeProvider,
    StaticKnowledgeProvider,
)
from .adapters import IntelligenceKnowledgeAdapter, PersistenceKnowledgeAdapter

__all__ += [
    "KnowledgeMemoryRepository",
    "KnowledgeRepositoryManager",
    "build_memory_repository",
    "StaticKnowledgeProvider",
    "CharacterKnowledgeProvider",
    "GlossaryKnowledgeProvider",
    "NarrativeKnowledgeProvider",
    "SceneKnowledgeProvider",
    "RuntimeKnowledgeProvider",
    "IntelligenceKnowledgeAdapter",
    "PersistenceKnowledgeAdapter",
]
