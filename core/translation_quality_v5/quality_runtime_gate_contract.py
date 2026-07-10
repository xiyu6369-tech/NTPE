from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class QualityRuntimeGateContract:
    version = "TE-v5.2"
    stage = "5.2.1"

    def build_contract(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "gate_layer": "translation_quality_runtime_gate",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "decision_mode": "accept_reject_retry",
            "result_replacement_allowed": False,
            "provider_request_allowed": False,
            "real_translation_allowed": False,
            "runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "rollback_mode": "immediate_disable",
            "required_freezes": ["TE-v5.0", "TE-v5.1"],
            "required_components": [
                "TranslationQualityCorePipeline",
                "QualityRepairPipeline",
            ],
            "forbidden_inputs": [
                "api_key",
                "provider_client",
            ],
            "safety_guarantees": {
                "disabled_by_default": True,
                "single_chunk_only": True,
                "result_replacement_allowed": False,
                "provider_request_allowed": False,
                "real_translation_allowed": False,
                "rollback_available": True,
            },
        }

    def validate_contract(self, contract: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(contract, Mapping):
            return False
        required = {
            "version", "stage", "gate_layer", "default_mode",
            "activation_mode", "allowed_caller", "allowed_scope",
            "max_chunks_per_request", "decision_mode",
            "result_replacement_allowed", "provider_request_allowed",
            "real_translation_allowed", "runtime_touch_mode",
            "launcher_touch_mode", "rollback_mode",
            "required_freezes", "required_components",
            "forbidden_inputs", "safety_guarantees",
        }
        if not required.issubset(contract):
            return False
        if contract.get("version") != self.version or contract.get("stage") != self.stage:
            return False
        if contract.get("default_mode") != "disabled":
            return False
        if contract.get("activation_mode") != "explicit_opt_in_only":
            return False
        if contract.get("allowed_caller") != "translation_runtime":
            return False
        if contract.get("allowed_scope") != "single_chunk":
            return False
        if contract.get("max_chunks_per_request") != 1:
            return False
        if contract.get("decision_mode") != "accept_reject_retry":
            return False
        if contract.get("result_replacement_allowed") is not False:
            return False
        if contract.get("provider_request_allowed") is not False:
            return False
        if contract.get("real_translation_allowed") is not False:
            return False
        if contract.get("runtime_touch_mode") != "none":
            return False
        if contract.get("launcher_touch_mode") != "none":
            return False
        if contract.get("rollback_mode") != "immediate_disable":
            return False
        if set(contract.get("required_freezes", [])) != {"TE-v5.0", "TE-v5.1"}:
            return False
        return True

    def describe_gate(self) -> Dict[str, Any]:
        return {
            "current_stage": self.stage,
            "current_mode": "contract_only",
            "enabled_by_default": False,
            "allowed_scope": "single_chunk",
            "decision_mode": "accept_reject_retry",
            "result_replacement_allowed": False,
            "provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
        }
