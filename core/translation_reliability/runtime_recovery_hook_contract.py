from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class TranslationRuntimeRecoveryHookContract:
    """Contract for the translation-runtime recovery hook pilot.

    This stage defines a shadow-only hook boundary. It does not execute
    recovery, call providers, replace runtime results, or touch launcher code.
    """

    version = "TE-v4.3"
    stage = "4.3.1"
    name = "translation_runtime_recovery_hook_contract"

    required_freezes = ["TE-v4.0", "TE-v4.1", "TE-v4.2"]
    required_components = [
        "RealRuntimeRecoveryPilotAdmissionGate",
        "RealRuntimeRecoveryPilotRollbackController",
        "RealRuntimeRecoveryPilotDryRunRunner",
        "RealRuntimeRecoveryPilotDryRunBundle",
    ]

    def build_contract(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "hook_layer": "translation_runtime_recovery_hook",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "shadow_only",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_hook": 1,
            "max_recovery_flows_per_chunk": 1,
            "result_replacement_allowed": False,
            "provider_fallback_allowed": False,
            "real_provider_request_allowed": False,
            "launcher_touch_mode": "none",
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "optional_hook_only",
            "rollback_mode": "immediate_disable",
            "required_freezes": list(self.required_freezes),
            "required_components": list(self.required_components),
            "metadata": {
                "contract": self.name,
                "version": self.version,
                "stage": self.stage,
                "runtime_main_flow_modified": False,
            },
        }

    def validate_contract(self, contract: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(contract, Mapping):
            return False
        expected = {
            "version": self.version,
            "stage": self.stage,
            "hook_layer": "translation_runtime_recovery_hook",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "shadow_only",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_hook": 1,
            "max_recovery_flows_per_chunk": 1,
            "result_replacement_allowed": False,
            "provider_fallback_allowed": False,
            "real_provider_request_allowed": False,
            "launcher_touch_mode": "none",
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "optional_hook_only",
            "rollback_mode": "immediate_disable",
        }
        for key, value in expected.items():
            if contract.get(key) != value:
                return False
        if set(contract.get("required_freezes", [])) != set(self.required_freezes):
            return False
        if set(contract.get("required_components", [])) != set(self.required_components):
            return False
        return isinstance(contract.get("metadata"), Mapping)

    def describe_hook(self) -> Dict[str, Any]:
        return {
            "current_stage": self.stage,
            "current_mode": "shadow_only",
            "enabled_by_default": False,
            "allowed_scope": "single_chunk",
            "max_chunks_per_hook": 1,
            "result_replacement_allowed": False,
            "provider_fallback_allowed": False,
            "real_provider_request_allowed": False,
            "rollback_available": True,
            "translation_runtime_main_flow_modified": False,
            "provider_runtime_modified": False,
            "launcher_modified": False,
        }


__all__ = ["TranslationRuntimeRecoveryHookContract"]
