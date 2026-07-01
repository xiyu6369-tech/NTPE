"""Foundation-07 Translation Intelligence public API."""

from .adapter import IntelligenceAdapter
from .character_engine import CharacterMemoryEngine
from .consistency import ConsistencyContract
from .consistency_engine import ConsistencyEngine
from .contracts import (
    CharacterMemoryEntry,
    ConsistencyIssue,
    GlossaryEntry,
    IntelligenceSnapshot,
    NarrativeMemoryEntry,
    SceneMemoryEntry,
)
from .engine import TranslationIntelligenceEngine
from .glossary_engine import GlossaryIntelligenceEngine
from .lifecycle import TranslationIntelligenceLifecycle
from .memory_store import IntelligenceMemoryStore
from .merge_strategy import IntelligenceMergeStrategy
from .narrative_engine import NarrativeMemoryEngine

from .events import (
    IntelligenceEvent,
    IntelligenceEventBus,
    IntelligenceEventDispatcher,
    IntelligencePublisher,
    IntelligenceRuntimeEventFacade,
    IntelligenceSubscriber,
)

from .persistence import (
    IntelligencePersistenceLoader,
    IntelligencePersistenceRegistry,
    IntelligenceSnapshotSerializer,
    JsonIntelligenceStore,
    SQLiteIntelligenceStore,
    get_default_persistence_registry,
)
from .persistence_contract import IntelligencePersistenceContract, InMemoryIntelligencePersistence
from .runtime_integration import RuntimeIntelligencePacket, TranslationIntelligenceRuntimeIntegration
from .scene_engine import SceneMemoryEngine
from .session_scope import IntelligenceSessionScope
from .snapshot_manager import IntelligenceSnapshotManager
from .versioning import SnapshotVersion

__all__ = [
    "CharacterMemoryEngine",
    "CharacterMemoryEntry",
    "ConsistencyContract",
    "ConsistencyEngine",
    "ConsistencyIssue",
    "GlossaryEntry",
    "GlossaryIntelligenceEngine",
    "IntelligenceAdapter",
    "IntelligenceEvent",
    "IntelligenceEventBus",
    "IntelligenceEventDispatcher",
    "IntelligencePublisher",
    "IntelligenceRuntimeEventFacade",
    "IntelligenceSubscriber",
    "IntelligenceMemoryStore",
    "IntelligenceMergeStrategy",
    "IntelligencePersistenceContract",
    "IntelligencePersistenceLoader",
    "IntelligencePersistenceRegistry",
    "IntelligenceSessionScope",
    "IntelligenceSnapshot",
    "IntelligenceSnapshotManager",
    "IntelligenceSnapshotSerializer",
    "InMemoryIntelligencePersistence",
    "JsonIntelligenceStore",
    "NarrativeMemoryEngine",
    "NarrativeMemoryEntry",
    "RuntimeIntelligencePacket",
    "SQLiteIntelligenceStore",
    "SceneMemoryEngine",
    "SceneMemoryEntry",
    "SnapshotVersion",
    "TranslationIntelligenceEngine",
    "TranslationIntelligenceLifecycle",
    "TranslationIntelligenceRuntimeIntegration",
    "get_default_persistence_registry",
]
