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
