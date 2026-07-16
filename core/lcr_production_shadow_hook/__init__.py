"""LCR Batch 10.1 single read-only Production shadow hook."""

from .evidence_sink import AtomicTestFileEvidenceSink, DisabledEvidenceSink, InMemoryEvidenceSink
from .bounded_execution import executor_snapshot, wait_for_shadow_idle
from .character_memory_shadow import (
    DEFAULT_SHADOW_SELECTION_BUDGET, SUPPORTED_PROFILES,
    build_character_memory_shadow_input, empty_character_memory_result,
    evaluate_character_memory_shadow,
)
from .feature_flags import CHARACTER_MEMORY_FLAG, GLOBAL_FLAG, KILL_SWITCH, minimal_shadow_flags, resolve_hook_flags
from .hook import CALLER_WAIT_BUDGET_MS, HARD_BUDGET_MS, SOFT_BUDGET_MS, run_read_only_lcr_shadow_hook
from .models import (
    CharacterMemoryShadowInput, CharacterMemoryShadowResult,
    ExtendedShadowGate, HookEvidence, HookOutcome, HOOK_SYMBOL, HOOK_VERSION,
)
from .validation import evaluate_character_memory_shadow_gate, evaluate_extended_shadow_gate

__all__ = [name for name in globals() if not name.startswith("_")]
