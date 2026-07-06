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
