# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

try:
    from .context_engine import ContextIntelligenceEngine
    from .context_events import (
        CONTEXT_COMPLETED,
        CONTEXT_COMPRESSED,
        CONTEXT_STARTED,
        ContextEvent,
        ContextEventBus,
    )
    from .context_exceptions import ContextIntelligenceError, ContextWindowError
    from .context_graph import ContextGraph
    from .context_memory import ContextMemory
    from .context_metrics import build_context_metrics
    from .context_pipeline import ContextPipeline
    from .context_registry import ContextRegistry
    from .context_result import ContextEdge, ContextIntelligenceResult, ContextItem
    from .context_window import ContextWindow
except Exception:
    ContextIntelligenceEngine = None
    ContextEvent = None
    ContextEventBus = None
    ContextGraph = None
    ContextMemory = None
    ContextPipeline = None
    ContextRegistry = None
    ContextEdge = None
    ContextIntelligenceResult = None
    ContextItem = None
    ContextWindow = None
    ContextIntelligenceError = None
    ContextWindowError = None
    build_context_metrics = None
    CONTEXT_COMPLETED = "ContextCompleted"
    CONTEXT_COMPRESSED = "ContextCompressed"
    CONTEXT_STARTED = "ContextStarted"

__all__ = [
    "CONTEXT_COMPLETED",
    "CONTEXT_COMPRESSED",
    "CONTEXT_STARTED",
    "ContextEdge",
    "ContextEvent",
    "ContextEventBus",
    "ContextGraph",
    "ContextIntelligenceEngine",
    "ContextIntelligenceError",
    "ContextIntelligenceResult",
    "ContextItem",
    "ContextMemory",
    "ContextPipeline",
    "ContextRegistry",
    "ContextWindow",
    "ContextWindowError",
    "build_context_metrics",
]

# Stage-16.2 Narrative Intelligence exports
try:
    from .narrative_context import NarrativeContext
    from .narrative_engine import NarrativeIntelligenceEngine
    from .narrative_events import (
        NARRATIVE_ANALYZED,
        NARRATIVE_COMPLETED,
        NARRATIVE_STARTED,
        NarrativeEvent,
        NarrativeEventBus,
    )
    from .narrative_exceptions import NarrativeInputError, NarrativeIntelligenceError
    from .narrative_metrics import build_narrative_metrics
    from .narrative_pipeline import NarrativePipeline
    from .narrative_profile import build_style_profile
    from .narrative_result import NarrativeFinding, NarrativeIntelligenceResult, NarrativeSegment
    from .narrative_rules import (
        detect_emotional_tone,
        detect_perspective,
        detect_scene_transitions,
        detect_tense,
        detect_voice,
        split_segments,
    )
    from .narrative_state import NarrativeState
except Exception:
    NarrativeContext = None
    NarrativeIntelligenceEngine = None
    NarrativeEvent = None
    NarrativeEventBus = None
    NarrativeInputError = None
    NarrativeIntelligenceError = None
    NarrativePipeline = None
    NarrativeFinding = None
    NarrativeIntelligenceResult = None
    NarrativeSegment = None
    NarrativeState = None
    build_narrative_metrics = None
    build_style_profile = None
    detect_emotional_tone = None
    detect_perspective = None
    detect_scene_transitions = None
    detect_tense = None
    detect_voice = None
    split_segments = None
    NARRATIVE_ANALYZED = "NarrativeAnalyzed"
    NARRATIVE_COMPLETED = "NarrativeCompleted"
    NARRATIVE_STARTED = "NarrativeStarted"

__all__.extend([
    "NARRATIVE_ANALYZED",
    "NARRATIVE_COMPLETED",
    "NARRATIVE_STARTED",
    "NarrativeContext",
    "NarrativeEvent",
    "NarrativeEventBus",
    "NarrativeFinding",
    "NarrativeInputError",
    "NarrativeIntelligenceEngine",
    "NarrativeIntelligenceError",
    "NarrativeIntelligenceResult",
    "NarrativePipeline",
    "NarrativeSegment",
    "NarrativeState",
    "build_narrative_metrics",
    "build_style_profile",
    "detect_emotional_tone",
    "detect_perspective",
    "detect_scene_transitions",
    "detect_tense",
    "detect_voice",
    "split_segments",
])


# Stage-16.3 Character Relationship Intelligence exports
try:
    from .character_alias import build_alias_index, detect_alias_conflicts
    from .character_engine import CharacterRelationshipIntelligenceEngine
    from .character_events import (
        CHARACTER_ANALYZED,
        CHARACTER_COMPLETED,
        CHARACTER_STARTED,
        CharacterEvent,
        CharacterEventBus,
    )
    from .character_exceptions import CharacterInputError, CharacterIntelligenceError
    from .character_graph import CharacterGraph
    from .character_memory import CharacterMemory
    from .character_metrics import build_character_metrics
    from .character_pipeline import CharacterPipeline
    from .character_pronoun import detect_pronouns, resolve_pronouns
    from .character_registry import CharacterRecord, CharacterRegistry
    from .character_relationship import CharacterRelationship
    from .character_result import CharacterFinding, CharacterIntelligenceResult, CharacterMention
except Exception:
    CharacterRelationshipIntelligenceEngine = None
    CharacterEvent = None
    CharacterEventBus = None
    CharacterGraph = None
    CharacterMemory = None
    CharacterPipeline = None
    CharacterRecord = None
    CharacterRegistry = None
    CharacterRelationship = None
    CharacterFinding = None
    CharacterIntelligenceResult = None
    CharacterMention = None
    CharacterInputError = None
    CharacterIntelligenceError = None
    build_alias_index = None
    build_character_metrics = None
    detect_alias_conflicts = None
    detect_pronouns = None
    resolve_pronouns = None
    CHARACTER_ANALYZED = "CharacterAnalyzed"
    CHARACTER_COMPLETED = "CharacterCompleted"
    CHARACTER_STARTED = "CharacterStarted"

__all__.extend([
    "CHARACTER_ANALYZED",
    "CHARACTER_COMPLETED",
    "CHARACTER_STARTED",
    "CharacterEvent",
    "CharacterEventBus",
    "CharacterFinding",
    "CharacterGraph",
    "CharacterInputError",
    "CharacterIntelligenceError",
    "CharacterIntelligenceResult",
    "CharacterMemory",
    "CharacterMention",
    "CharacterPipeline",
    "CharacterRecord",
    "CharacterRegistry",
    "CharacterRelationship",
    "CharacterRelationshipIntelligenceEngine",
    "build_alias_index",
    "build_character_metrics",
    "detect_alias_conflicts",
    "detect_pronouns",
    "resolve_pronouns",
])


# Stage-16.4 Semantic Consistency Engine exports
try:
    from .semantic_engine import SemanticConsistencyEngine
    from .semantic_events import (
        SEMANTIC_ANALYZED,
        SEMANTIC_COMPLETED,
        SEMANTIC_STARTED,
        SemanticEvent,
        SemanticEventBus,
    )
    from .semantic_exceptions import SemanticInputError, SemanticIntelligenceError
    from .semantic_graph import SemanticEdge, SemanticGraph
    from .semantic_memory import SemanticMemory
    from .semantic_metrics import build_semantic_metrics
    from .semantic_pipeline import SemanticConsistencyPipeline
    from .semantic_result import SemanticConsistencyResult, SemanticFinding, SemanticUnit
    from .semantic_rules import (
        build_concept_map,
        build_event_map,
        build_semantic_units,
        detect_continuity_gaps,
        detect_semantic_contradictions,
        extract_concepts,
        extract_events,
    )
except Exception:
    SemanticConsistencyEngine = None
    SemanticEvent = None
    SemanticEventBus = None
    SemanticEdge = None
    SemanticGraph = None
    SemanticMemory = None
    SemanticConsistencyPipeline = None
    SemanticConsistencyResult = None
    SemanticFinding = None
    SemanticUnit = None
    SemanticInputError = None
    SemanticIntelligenceError = None
    build_concept_map = None
    build_event_map = None
    build_semantic_metrics = None
    build_semantic_units = None
    detect_continuity_gaps = None
    detect_semantic_contradictions = None
    extract_concepts = None
    extract_events = None
    SEMANTIC_ANALYZED = "SemanticAnalyzed"
    SEMANTIC_COMPLETED = "SemanticCompleted"
    SEMANTIC_STARTED = "SemanticStarted"

__all__.extend([
    "SEMANTIC_ANALYZED",
    "SEMANTIC_COMPLETED",
    "SEMANTIC_STARTED",
    "SemanticConsistencyEngine",
    "SemanticConsistencyPipeline",
    "SemanticConsistencyResult",
    "SemanticEdge",
    "SemanticEvent",
    "SemanticEventBus",
    "SemanticFinding",
    "SemanticGraph",
    "SemanticInputError",
    "SemanticIntelligenceError",
    "SemanticMemory",
    "SemanticUnit",
    "build_concept_map",
    "build_event_map",
    "build_semantic_metrics",
    "build_semantic_units",
    "detect_continuity_gaps",
    "detect_semantic_contradictions",
    "extract_concepts",
    "extract_events",
])

# Stage-16.5 Translation Memory Intelligence
try:
    from .translation_memory_engine import TranslationMemoryIntelligenceEngine
    from .translation_memory_entry import TranslationMemoryEntry
    from .translation_memory_result import TranslationMemoryMatch, TranslationMemoryResult
except Exception:  # pragma: no cover - compatibility-safe optional exports
    pass

# Stage-16.6 Adaptive Translation Strategy exports
try:
    from .adaptive_strategy_context import AdaptiveStrategyContext
    from .adaptive_strategy_engine import AdaptiveTranslationStrategyEngine
    from .adaptive_strategy_events import (
        STRATEGY_COMPLETED,
        STRATEGY_SELECTED,
        STRATEGY_STARTED,
        AdaptiveStrategyEvent,
        AdaptiveStrategyEventBus,
    )
    from .adaptive_strategy_exceptions import AdaptiveStrategyError, AdaptiveStrategyInputError
    from .adaptive_strategy_pipeline import AdaptiveStrategyPipeline
    from .adaptive_strategy_policy import AdaptiveStrategyPolicy
    from .adaptive_strategy_profile import AdaptiveStrategyProfile, default_strategy_profiles
    from .adaptive_strategy_result import AdaptiveStrategyCandidate, AdaptiveStrategyResult
    from .adaptive_strategy_selector import AdaptiveStrategySelector, classify_content
except Exception:  # pragma: no cover - compatibility-safe optional exports
    pass

try:
    __all__.extend([
        "STRATEGY_COMPLETED",
        "STRATEGY_SELECTED",
        "STRATEGY_STARTED",
        "AdaptiveStrategyCandidate",
        "AdaptiveStrategyContext",
        "AdaptiveStrategyEngine",
        "AdaptiveStrategyError",
        "AdaptiveStrategyEvent",
        "AdaptiveStrategyEventBus",
        "AdaptiveStrategyInputError",
        "AdaptiveStrategyPipeline",
        "AdaptiveStrategyPolicy",
        "AdaptiveStrategyProfile",
        "AdaptiveStrategyResult",
        "AdaptiveStrategySelector",
        "AdaptiveTranslationStrategyEngine",
        "classify_content",
        "default_strategy_profiles",
    ])
except Exception:
    pass


# Stage-16.7 Intelligence Runtime Integration exports
try:
    from .intelligence_runtime import IntelligenceRuntime
    from .intelligence_runtime_context import IntelligenceRuntimeContext
    from .intelligence_runtime_events import (
        INTELLIGENCE_RUNTIME_COMPLETED,
        INTELLIGENCE_RUNTIME_STARTED,
        INTELLIGENCE_RUNTIME_STEP_COMPLETED,
        IntelligenceRuntimeEvent,
        IntelligenceRuntimeEventBus,
    )
    from .intelligence_runtime_exceptions import IntelligenceRuntimeError, IntelligenceRuntimeInputError
    from .intelligence_runtime_pipeline import IntelligenceRuntimePipeline
    from .intelligence_runtime_registry import IntelligenceRuntimeRegistry
    from .intelligence_runtime_result import IntelligenceRuntimeResult
except Exception:  # pragma: no cover - compatibility-safe optional exports
    pass

try:
    __all__.extend([
        "INTELLIGENCE_RUNTIME_COMPLETED",
        "INTELLIGENCE_RUNTIME_STARTED",
        "INTELLIGENCE_RUNTIME_STEP_COMPLETED",
        "IntelligenceRuntime",
        "IntelligenceRuntimeContext",
        "IntelligenceRuntimeError",
        "IntelligenceRuntimeEvent",
        "IntelligenceRuntimeEventBus",
        "IntelligenceRuntimeInputError",
        "IntelligenceRuntimePipeline",
        "IntelligenceRuntimeRegistry",
        "IntelligenceRuntimeResult",
    ])
except Exception:
    pass

# Stage-16.8 Advanced Translation Intelligence Freeze exports
try:
    from .intelligence_contract import IntelligenceRuntimeContract
    from .intelligence_freeze_events import (
        INTELLIGENCE_FREEZE_COMPLETED,
        INTELLIGENCE_FREEZE_STARTED,
        INTELLIGENCE_FREEZE_VALIDATED,
        IntelligenceFreezeEvent,
        IntelligenceFreezeEventBus,
    )
    from .intelligence_freeze_manifest import IntelligenceFreezeManifest
    from .intelligence_freeze_result import IntelligenceFreezeResult
    from .intelligence_freeze_validator import IntelligenceFreezeValidator
except Exception:
    IntelligenceRuntimeContract = None
    IntelligenceFreezeEvent = None
    IntelligenceFreezeEventBus = None
    IntelligenceFreezeManifest = None
    IntelligenceFreezeResult = None
    IntelligenceFreezeValidator = None
    INTELLIGENCE_FREEZE_COMPLETED = "IntelligenceFreezeCompleted"
    INTELLIGENCE_FREEZE_STARTED = "IntelligenceFreezeStarted"
    INTELLIGENCE_FREEZE_VALIDATED = "IntelligenceFreezeValidated"

__all__.extend([
    "INTELLIGENCE_FREEZE_COMPLETED",
    "INTELLIGENCE_FREEZE_STARTED",
    "INTELLIGENCE_FREEZE_VALIDATED",
    "IntelligenceFreezeEvent",
    "IntelligenceFreezeEventBus",
    "IntelligenceFreezeManifest",
    "IntelligenceFreezeResult",
    "IntelligenceFreezeValidator",
    "IntelligenceRuntimeContract",
])
