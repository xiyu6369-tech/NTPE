"""
NTPE Foundation-04.3
Pipeline Contract Adapter

Additive adapter that can be inserted before/after existing pipeline stages.
It does not replace Foundation-04.2 migration behavior.
"""

from __future__ import annotations

from typing import Any, Mapping, Dict

from core.context_contract import (
    validate_context_payload,
    normalize_context_payload,
    NTPEContextContractError,
)


class PipelineContextContractAdapter:
    name = "pipeline_context_contract_adapter"
    foundation = "04.3"

    def before_stage(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        result = validate_context_payload(payload)
        return result.payload

    def after_stage(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        result = validate_context_payload(payload)
        return result.payload

    def normalize(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return normalize_context_payload(payload)

    def __call__(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return self.normalize(payload)
