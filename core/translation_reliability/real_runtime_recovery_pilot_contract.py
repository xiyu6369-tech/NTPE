from __future__ import annotations

from typing import Any, Dict, Mapping, Optional


class RealRuntimeRecoveryPilotContract:
    """Contract for the first tightly scoped real-runtime recovery pilot.

    Stage 4.2.1 only defines the boundary. It does not call recovery flows,
    providers, HTTP clients, launcher code, or Translation Runtime.
    """

    version = "TE-v4.2"
    stage = "4.2.1"
    name = "real_runtime_recovery_pilot_contract"

    required_freezes = ["TE-v4.0", "TE-v4.1"]
    required_components = [
        "RecoveryFlowIntegration",
        "RuntimeRecoveryHookAdapter",
        "AdaptiveRetryExecutionHarness",
        "RecoveryOutcomeGuard",
        "RecoveryResultBundle",
    ]
    allowed_inputs = [
        "runtime_id",
        "chunk_index",
        "source_chars",
        "failure_outcome",
        "retry_count",
        "provider_attempts",
        "latency_ms",
        "config",
        "metadata",
    ]
    forbidden_inputs = [
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    ]
    expected_outputs = [
        "pilot_status",
        "admission_status",
        "recovery_status",
        "rollback_status",
        "metadata",
    ]

    def build_contract(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "pilot_layer": "real_runtime_recovery_pilot",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "contract_only",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "max_recovery_flows_per_chunk": 1,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "rollback_mode": "immediate_disable",
            "required_freezes": list(self.required_freezes),
            "required_components": list(self.required_components),
            "allowed_inputs": list(self.allowed_inputs),
            "forbidden_inputs": list(self.forbidden_inputs),
            "expected_outputs": list(self.expected_outputs),
            "safety_guarantees": {
                "disabled_by_default": True,
                "explicit_opt_in_required": True,
                "single_chunk_only": True,
                "execution_allowed": False,
                "real_provider_request_allowed": False,
                "real_translation_allowed": False,
                "rollback_available": True,
                "provider_runtime_unchanged": True,
                "translation_runtime_unchanged": True,
                "launcher_unchanged": True,
            },
            "metadata": {
                "contract": self.name,
                "version": self.version,
                "stage": self.stage,
                "runtime_touch": "contract_only",
            },
        }

    def validate_contract(self, contract: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(contract, Mapping):
            return False

        expected_scalars = {
            "version": self.version,
            "stage": self.stage,
            "pilot_layer": "real_runtime_recovery_pilot",
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "contract_only",
            "allowed_caller": "translation_runtime",
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "max_recovery_flows_per_chunk": 1,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "provider_runtime_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "rollback_mode": "immediate_disable",
        }
        for key, expected in expected_scalars.items():
            if contract.get(key) != expected:
                return False

        if set(contract.get("required_freezes", [])) != set(self.required_freezes):
            return False
        if set(contract.get("required_components", [])) != set(self.required_components):
            return False
        if not set(self.forbidden_inputs).issubset(contract.get("forbidden_inputs", [])):
            return False
        if not set(self.allowed_inputs).issubset(contract.get("allowed_inputs", [])):
            return False
        if not set(self.expected_outputs).issubset(contract.get("expected_outputs", [])):
            return False

        guarantees = contract.get("safety_guarantees")
        if not isinstance(guarantees, Mapping):
            return False
        expected_guarantees = {
            "disabled_by_default": True,
            "explicit_opt_in_required": True,
            "single_chunk_only": True,
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "provider_runtime_unchanged": True,
            "translation_runtime_unchanged": True,
            "launcher_unchanged": True,
        }
        for key, expected in expected_guarantees.items():
            if guarantees.get(key) is not expected:
                return False

        return isinstance(contract.get("metadata"), Mapping)

    def describe_pilot(self) -> Dict[str, Any]:
        return {
            "current_stage": self.stage,
            "current_mode": "contract_only",
            "enabled_by_default": False,
            "allowed_scope": "single_chunk",
            "max_chunks_per_request": 1,
            "execution_allowed": False,
            "real_provider_request_allowed": False,
            "real_translation_allowed": False,
            "rollback_available": True,
            "provider_runtime_modified": False,
            "translation_runtime_modified": False,
            "launcher_modified": False,
        }


__all__ = ["RealRuntimeRecoveryPilotContract"]
