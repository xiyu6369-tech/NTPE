"""
NTPE Foundation-04.5
Pipeline Execution Trace Adapter

Additive adapter for attaching and recording auditable execution trace events.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.pipeline_execution_trace import (
    append_trace_event,
    attach_trace_to_state,
    begin_trace_stage,
    complete_trace_stage,
    create_execution_trace,
    fail_trace_stage,
    normalize_execution_trace,
    record_trace_adapter,
    record_trace_plugin,
    state_trace_event,
    validate_execution_trace,
)


class PipelineExecutionTraceAdapter:
    name = "pipeline_execution_trace_adapter"
    foundation = "04.5"

    def create(self, *, trace_id: Optional[str] = None) -> Dict[str, Any]:
        return create_execution_trace(trace_id=trace_id)

    def normalize(self, trace: Mapping[str, Any]) -> Dict[str, Any]:
        return normalize_execution_trace(trace)

    def validate(self, trace: Mapping[str, Any]) -> Dict[str, Any]:
        return validate_execution_trace(trace).trace

    def attach(self, state: Mapping[str, Any], trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return attach_trace_to_state(state, trace)

    def event(
        self,
        trace: Mapping[str, Any],
        event_type: str,
        status: str,
        *,
        name: Optional[str] = None,
        message: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return append_trace_event(trace, event_type, status, name=name, message=message, metadata=metadata)

    def before_stage(self, trace: Mapping[str, Any], stage: str) -> Dict[str, Any]:
        return begin_trace_stage(trace, stage)

    def after_stage(self, trace: Mapping[str, Any], stage: str) -> Dict[str, Any]:
        return complete_trace_stage(trace, stage)

    def on_error(self, trace: Mapping[str, Any], stage: str, error: Any) -> Dict[str, Any]:
        return fail_trace_stage(trace, stage, error)

    def plugin(self, trace: Mapping[str, Any], plugin_name: str, event: str = "applied") -> Dict[str, Any]:
        return record_trace_plugin(trace, plugin_name, event)

    def adapter(self, trace: Mapping[str, Any], adapter_name: str, event: str = "applied") -> Dict[str, Any]:
        return record_trace_adapter(trace, adapter_name, event)

    def state_event(
        self,
        state: Mapping[str, Any],
        event_type: str,
        status: str,
        *,
        name: Optional[str] = None,
        message: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return state_trace_event(state, event_type, status, name=name, message=message, metadata=metadata)

    def __call__(self, trace: Mapping[str, Any]) -> Dict[str, Any]:
        return self.normalize(trace)
