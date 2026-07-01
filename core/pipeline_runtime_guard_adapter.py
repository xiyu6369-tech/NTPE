"""
NTPE Foundation-04.6
Pipeline Runtime Guard Adapter

Additive adapter wrapper for validating payload/state/trace/runtime data before
and after pipeline stages, plugins, and adapters.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from core.pipeline_runtime_guard import (
    RuntimeGuardResult,
    guard_after_stage,
    guard_before_stage,
    guard_failure,
    guard_payload,
    guard_runtime,
    guard_state,
    guard_trace,
    guarded_call,
)


class PipelineRuntimeGuardAdapter:
    name = "pipeline_runtime_guard_adapter"
    foundation = "04.6"

    def payload(self, payload: Mapping[str, Any], *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
        return guard_payload(payload, phase=phase, strict=strict)

    def state(self, state: Mapping[str, Any], *, phase: str = "validate", strict: bool = False, ensure_trace: bool = True) -> RuntimeGuardResult:
        return guard_state(state, phase=phase, strict=strict, ensure_trace=ensure_trace)

    def trace(self, trace: Optional[Mapping[str, Any]] = None, *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
        return guard_trace(trace, phase=phase, strict=strict)

    def runtime(self, runtime: Mapping[str, Any], *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
        return guard_runtime(runtime, phase=phase, strict=strict)

    def before_stage(self, state: Mapping[str, Any], stage: str, *, strict: bool = False) -> Dict[str, Any]:
        return guard_before_stage(state, stage, strict=strict)

    def after_stage(self, state: Mapping[str, Any], stage: str, *, strict: bool = False) -> Dict[str, Any]:
        return guard_after_stage(state, stage, strict=strict)

    def failure(self, state: Mapping[str, Any], stage: str, error: Any, *, strict: bool = False) -> Dict[str, Any]:
        return guard_failure(state, stage, error, strict=strict)

    def call(self, state: Mapping[str, Any], stage: str, fn: Callable[[Dict[str, Any]], Mapping[str, Any]], *, strict: bool = False) -> Dict[str, Any]:
        return guarded_call(state, stage, fn, strict=strict)

    def __call__(self, state: Mapping[str, Any]) -> RuntimeGuardResult:
        return self.state(state)
