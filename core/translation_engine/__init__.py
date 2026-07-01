"""NTPE 1.0 Beta Stage-02 Translation Engine.

Additive product-layer translation engine built on Foundation v1.0 and
Stage-01 Production Runtime. It does not modify frozen Foundation contracts.
"""
from .diagnostics import TranslationDiagnostics
from .events import TranslationEvent, TranslationEventBus
from .manifest import VERSION, build_translation_engine_manifest
from .metrics import TranslationMetrics
from .orchestrator import TranslationOrchestrator
from .pipeline import TranslationPipeline, TranslationPipelineContext
from .recovery import TranslationRecoveryManager, TranslationRecoveryResult
from .session import TranslationSession, TranslationSessionManager
from .strategy import TranslationStrategy
from .validator import TranslationValidator, ValidationIssue, ValidationResult

__all__ = [
    "TranslationDiagnostics",
    "TranslationEvent",
    "TranslationEventBus",
    "VERSION",
    "build_translation_engine_manifest",
    "TranslationMetrics",
    "TranslationOrchestrator",
    "TranslationPipeline",
    "TranslationPipelineContext",
    "TranslationRecoveryManager",
    "TranslationRecoveryResult",
    "TranslationSession",
    "TranslationSessionManager",
    "TranslationStrategy",
    "TranslationValidator",
    "ValidationIssue",
    "ValidationResult",
]
