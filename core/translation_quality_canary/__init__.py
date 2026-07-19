"""TE v7.2 Stage 12.5.1 offline controlled-canary verification harness."""

from .comparison import CHECKLIST, COMPARISON_VALUES, build_comparison_report
from .fixtures import build_offline_canary_stores
from .models import CanaryArmRecord, CanaryConfiguration, CanaryPairRecord
from .runner import BASELINE_FLAGS, CANDIDATE_FLAGS, run_offline_canary_case


ACTIVATION_GATE_READY = "translation_quality_integration_ready_for_controlled_canary"
ACTIVATION_GATE_PASSED = "translation_quality_integration_canary_passed"

__all__ = [
    "ACTIVATION_GATE_PASSED",
    "ACTIVATION_GATE_READY",
    "BASELINE_FLAGS",
    "CANDIDATE_FLAGS",
    "CHECKLIST",
    "COMPARISON_VALUES",
    "CanaryArmRecord",
    "CanaryConfiguration",
    "CanaryPairRecord",
    "build_comparison_report",
    "build_offline_canary_stores",
    "run_offline_canary_case",
]
