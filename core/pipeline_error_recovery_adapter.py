"""
NTPE Foundation-04.7
Pipeline Error Recovery Adapter

Additive adapter wrapper for creating, attaching, and applying recovery decisions
without changing Foundation-04.6 runtime guard behavior.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from core.pipeline_error_recovery_contract import (
    RecoveryResult,
    apply_recovery,
    attach_recovery_to_state,
    classify_recovery_action,
    create_recovery_record,
    mark_recovery_applied,
    normalize_recovery_record,
    plan_recovery,
    recover_call,
    validate_recovery_record,
)


class PipelineErrorRecoveryAdapter:
    name = "pipeline_error_recovery_adapter"
    foundation = "04.7"

    def create(self, **kwargs: Any) -> Dict[str, Any]:
        return create_recovery_record(**kwargs)

    def normalize(self, record: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return normalize_recovery_record(record)

    def validate(self, record: Mapping[str, Any]) -> RecoveryResult:
        return validate_recovery_record(record)

    def classify(self, error: Any, *, attempt: int = 0, max_attempts: int = 3, fallback_available: bool = False) -> str:
        return classify_recovery_action(error, attempt=attempt, max_attempts=max_attempts, fallback_available=fallback_available)

    def attach(self, state: Mapping[str, Any], recovery: Mapping[str, Any]) -> Dict[str, Any]:
        return attach_recovery_to_state(state, recovery)

    def plan(self, state: Mapping[str, Any], stage: str, error: Any, **kwargs: Any) -> RecoveryResult:
        return plan_recovery(state, stage, error, **kwargs)

    def mark_applied(self, state: Mapping[str, Any], recovery: Optional[Mapping[str, Any]] = None, *, status: str = "applied") -> Dict[str, Any]:
        return mark_recovery_applied(state, recovery, status=status)

    def apply(self, state: Mapping[str, Any], recovery: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> RecoveryResult:
        return apply_recovery(state, recovery, **kwargs)

    def call(self, state: Mapping[str, Any], stage: str, fn: Callable[[Dict[str, Any]], Mapping[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        return recover_call(state, stage, fn, **kwargs)

    def __call__(self, state: Mapping[str, Any], stage: str, error: Any) -> RecoveryResult:
        return self.plan(state, stage, error)
