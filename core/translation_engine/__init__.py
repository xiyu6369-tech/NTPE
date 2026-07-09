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
from .context_intelligence import (
    CONTEXT_INTELLIGENCE_VERSION,
    apply_context_intelligence,
    build_context_directives,
    build_context_snapshot,
    build_naturalness_repair_directives,
    detect_context_profile,
    detect_naturalness_warnings,
    detect_unnatural_phrases,
)
from .prompt_intelligence import (
    PROMPT_INTELLIGENCE_VERSION,
    apply_prompt_intelligence,
    build_quality_directives,
    detect_text_profile,
    enhance_prompt_package,
)
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
    "CONTEXT_INTELLIGENCE_VERSION",
    "apply_context_intelligence",
    "build_context_directives",
    "build_context_snapshot",
    "build_naturalness_repair_directives",
    "detect_context_profile",
    "detect_naturalness_warnings",
    "detect_unnatural_phrases",
    "PROMPT_INTELLIGENCE_VERSION",
    "apply_prompt_intelligence",
    "build_quality_directives",
    "detect_text_profile",
    "enhance_prompt_package",
    "TranslationRecoveryManager",
    "TranslationRecoveryResult",
    "TranslationSession",
    "TranslationSessionManager",
    "TranslationStrategy",
    "TranslationValidator",
    "ValidationIssue",
    "ValidationResult",
]
