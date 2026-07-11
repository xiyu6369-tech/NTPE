from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class ControlledExecutionContract:
    """Safety contract for the v4.4 isolated controlled recovery pilot."""

    version = "TE-v4.4"
    stage = "4.4.1"
    name = "controlled_execution_contract"
    required_freezes = ["TE-v4.0", "TE-v4.1", "TE-v4.2", "TE-v4.3"]
    required_components = [
        "RuntimeHookAdmissionAdapter",
        "RuntimeSingleChunkShadowHook",
        "RuntimeHookResultMapper",
        "RealRuntimeRecoveryPilotRollbackController",
    ]
    forbidden_inputs = [
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    ]

    def build_contract(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "execution_layer": "translation_runtime_controlled_recovery",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "single_chunk_controlled",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "max_recovery_executions_per_chunk": 1,
            "result_replacement_mode": "guarded_controlled_only",
            "original_result_preserved": True,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "rollback_mode": "immediate_disable",
            "required_freezes": list(self.required_freezes),
            "required_components": list(self.required_components),
            "forbidden_inputs": list(self.forbidden_inputs),
            "safety_guarantees": {
                "disabled_by_default": True,
                "single_chunk_only": True,
                "original_result_preserved": True,
                "replacement_requires_guard": True,
                "real_provider_request_allowed": False,
                "provider_fallback_allowed": False,
                "real_translation_allowed": False,
                "rollback_available": True,
            },
            "metadata": {"contract": self.name, "version": self.version, "stage": self.stage},
        }

    def validate_contract(self, contract: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(contract, Mapping):
            return False
        expected = {
            "version": self.version,
            "stage": self.stage,
            "execution_layer": "translation_runtime_controlled_recovery",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "single_chunk_controlled",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "max_recovery_executions_per_chunk": 1,
            "result_replacement_mode": "guarded_controlled_only",
            "original_result_preserved": True,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "rollback_mode": "immediate_disable",
        }
        if any(contract.get(key) != value for key, value in expected.items()):
            return False
        if set(contract.get("required_freezes", [])) != set(self.required_freezes):
            return False
        if set(contract.get("required_components", [])) != set(self.required_components):
            return False
        if set(contract.get("forbidden_inputs", [])) != set(self.forbidden_inputs):
            return False
        guarantees = contract.get("safety_guarantees")
        required_guarantees = {
            "disabled_by_default": True,
            "single_chunk_only": True,
            "original_result_preserved": True,
            "replacement_requires_guard": True,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
        }
        return isinstance(guarantees, Mapping) and all(
            guarantees.get(key) is value for key, value in required_guarantees.items()
        ) and isinstance(contract.get("metadata"), Mapping)

    def describe_execution(self) -> Dict[str, Any]:
        return {
            "current_stage": self.stage,
            "current_mode": "single_chunk_controlled",
            "enabled_by_default": False,
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "result_replacement_mode": "guarded_controlled_only",
            "original_result_preserved": True,
            "replacement_requires_guard": True,
            "real_provider_request_allowed": False,
            "provider_fallback_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
        }


__all__ = ["ControlledExecutionContract"]
