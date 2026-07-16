"""LCR Batch 10.1 single read-only Production shadow hook."""

from .evidence_sink import AtomicTestFileEvidenceSink, DisabledEvidenceSink, InMemoryEvidenceSink
from .bounded_execution import executor_snapshot, wait_for_shadow_idle
from .feature_flags import GLOBAL_FLAG, KILL_SWITCH, minimal_shadow_flags, resolve_hook_flags
from .hook import CALLER_WAIT_BUDGET_MS, HARD_BUDGET_MS, SOFT_BUDGET_MS, run_read_only_lcr_shadow_hook
from .models import ExtendedShadowGate, HookEvidence, HookOutcome, HOOK_SYMBOL, HOOK_VERSION
from .validation import evaluate_extended_shadow_gate

__all__ = [name for name in globals() if not name.startswith("_")]
