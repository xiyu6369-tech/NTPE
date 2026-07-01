"""
NTPE Foundation-04.4
Pipeline State Adapter

Additive adapter for stages/plugins that need a stable execution state.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.pipeline_state_contract import (
    attach_payload_to_state,
    complete_stage_state,
    create_pipeline_state,
    fail_stage_state,
    normalize_pipeline_state,
    record_adapter_trace,
    record_plugin_trace,
    update_stage_state,
    validate_pipeline_state,
)


class PipelineStateAdapter:
    name = "pipeline_state_adapter"
    foundation = "04.4"

    def create(self, payload: Optional[Mapping[str, Any]] = None, *, stage: Optional[str] = None) -> Dict[str, Any]:
        return create_pipeline_state(payload, stage=stage)

    def normalize(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        return normalize_pipeline_state(state)

    def validate(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        return validate_pipeline_state(state).state

    def before_stage(self, state: Mapping[str, Any], stage: str) -> Dict[str, Any]:
        updated = update_stage_state(state, stage, "running")
        return record_adapter_trace(updated, self.name, "before_stage")

    def after_stage(self, state: Mapping[str, Any], stage: Optional[str] = None) -> Dict[str, Any]:
        updated = complete_stage_state(state, stage)
        return record_adapter_trace(updated, self.name, "after_stage")

    def on_error(self, state: Mapping[str, Any], stage: Optional[str], error: Any) -> Dict[str, Any]:
        updated = fail_stage_state(state, stage, error)
        return record_adapter_trace(updated, self.name, "error")

    def plugin(self, state: Mapping[str, Any], plugin_name: str, event: str = "applied") -> Dict[str, Any]:
        return record_plugin_trace(state, plugin_name, event)

    def attach_payload(self, state: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        return attach_payload_to_state(state, payload)

    def __call__(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        return self.normalize(state)
