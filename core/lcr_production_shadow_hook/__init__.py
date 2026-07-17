"""LCR Batch 10.1 single read-only Production shadow hook."""

from .evidence_sink import AtomicTestFileEvidenceSink, DisabledEvidenceSink, InMemoryEvidenceSink
from .bounded_execution import executor_snapshot, wait_for_shadow_idle
from .character_memory_shadow import (
    DEFAULT_SHADOW_SELECTION_BUDGET, SUPPORTED_PROFILES,
    build_character_memory_shadow_input, empty_character_memory_result,
    evaluate_character_memory_shadow,
)
from .context_scene_shadow import (
    DEFAULT_CONTEXT_SCENE_SHADOW_BUDGET, MAX_COMBINED_HYPOTHETICAL_BUDGET,
    build_context_scene_shadow_input, empty_context_scene_result, evaluate_context_scene_shadow,
)
from .dual_pass_semantic_shadow import build_dual_pass_semantic_shadow_input, empty_dual_pass_semantic_result, evaluate_dual_pass_semantic_shadow
from .feature_flags import CHARACTER_MEMORY_FLAG, CONTEXT_SCENE_FLAG, DUAL_PASS_SEMANTIC_FLAG, GLOBAL_FLAG, KILL_SWITCH, minimal_shadow_flags, resolve_hook_flags
from .hook import CALLER_WAIT_BUDGET_MS, HARD_BUDGET_MS, SOFT_BUDGET_MS, run_read_only_lcr_shadow_hook
from .models import (
    CharacterMemoryShadowInput, CharacterMemoryShadowResult, ContextSceneShadowInput, ContextSceneShadowResult, DualPassSemanticShadowInput, DualPassSemanticShadowResult,
    ExtendedShadowGate, HookEvidence, HookOutcome, HOOK_SYMBOL, HOOK_VERSION,
)
from .validation import evaluate_character_memory_shadow_gate, evaluate_context_scene_shadow_gate, evaluate_dual_pass_semantic_shadow_gate, evaluate_extended_shadow_gate
from .single_chunk_execution_authorization import SingleChunkExecutionAuthorization, authorization_fingerprint, seal_authorization, validate_execution_authorization
from .execution_review_result import ExecutionReviewResult, SingleChunkExecutionTarget
from .review_candidate_artifact import build_review_artifact, write_review_artifact
from .single_chunk_dual_pass_executor import EXECUTION_FLAG, PREPARATION_FLAG, execute_single_chunk_dual_pass_review, resolve_execution_flags

__all__ = [name for name in globals() if not name.startswith("_")]
