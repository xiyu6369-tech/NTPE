"""LCR Batch 10 metadata-only production integration shadow planning."""

from .activation_gate import evaluate_activation_gate
from .adapters import *
from .comparison import compare_baseline_shadow
from .feature_flags import DEFAULT_FLAGS, KILL_SWITCH, SHADOW_FLAGS, resolve_feature_flags
from .inventory import build_decision_matrix, build_integration_inventory
from .models import *
from .rollback import build_rollback_plan
from .serialization import canonical_json, deterministic_fingerprint, round_trip
from .shadow_input import create_shadow_input
from .shadow_runner import run_lcr_production_shadow
from .validation import resolve_allowed_path, validate_shadow_result

__all__ = [name for name in globals() if not name.startswith("_")]
