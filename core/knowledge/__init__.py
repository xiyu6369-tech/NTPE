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

# Foundation-08.2 Knowledge Runtime exports
from .runtime import (
    KnowledgeContextRuntime,
    KnowledgePromptRuntime,
    KnowledgeRepositoryRuntime,
    KnowledgeRuntime,
    KnowledgeSessionRuntime,
    build_knowledge_runtime_manifest,
)

__all__ += [
    "KnowledgeContextRuntime",
    "KnowledgePromptRuntime",
    "KnowledgeRepositoryRuntime",
    "KnowledgeRuntime",
    "KnowledgeSessionRuntime",
    "build_knowledge_runtime_manifest",
]

# Foundation-08.3 Knowledge Synchronization exports
from .synchronization import (
    KnowledgeConflictResolver,
    KnowledgeSyncContext,
    KnowledgeSyncRuntime,
    KnowledgeSyncSnapshot,
    KnowledgeSynchronizationManager,
    build_knowledge_synchronization_manifest,
    build_sync_context,
    build_sync_snapshot,
)

__all__ += [
    "KnowledgeConflictResolver",
    "KnowledgeSyncContext",
    "KnowledgeSyncRuntime",
    "KnowledgeSyncSnapshot",
    "KnowledgeSynchronizationManager",
    "build_knowledge_synchronization_manifest",
    "build_sync_context",
    "build_sync_snapshot",
]

# Foundation-08.4 Knowledge Cache exports
from .cache import (
    KnowledgeCacheEntry,
    KnowledgeCacheManager,
    KnowledgeCachePolicy,
    KnowledgeCacheRuntime,
    KnowledgeCacheSnapshot,
    KnowledgeCacheStore,
    build_knowledge_cache_manifest,
    build_lru_policy,
    build_ttl_policy,
)

__all__ += [
    "KnowledgeCacheEntry",
    "KnowledgeCacheManager",
    "KnowledgeCachePolicy",
    "KnowledgeCacheRuntime",
    "KnowledgeCacheSnapshot",
    "KnowledgeCacheStore",
    "build_knowledge_cache_manifest",
    "build_lru_policy",
    "build_ttl_policy",
]

# Foundation-08.5 Knowledge Query API exports
from .api import (
    KnowledgeAPI,
    KnowledgeFilter,
    KnowledgePagination,
    KnowledgeQueryBuilder,
    KnowledgeQueryExecutor,
    KnowledgeQueryRequest,
    KnowledgeQueryResult,
    KnowledgeSort,
    build_knowledge_api_manifest,
    build_query_request,
)

__all__ += [
    "KnowledgeAPI",
    "KnowledgeFilter",
    "KnowledgePagination",
    "KnowledgeQueryBuilder",
    "KnowledgeQueryExecutor",
    "KnowledgeQueryRequest",
    "KnowledgeQueryResult",
    "KnowledgeSort",
    "build_knowledge_api_manifest",
    "build_query_request",
]
