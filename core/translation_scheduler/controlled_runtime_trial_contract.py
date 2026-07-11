from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class ControlledRuntimeTrialContract:
    """Contract-only boundary for a future controlled Runtime integration trial."""

    version = "TE-v3.8"
    stage = "3.8.1"
    trial_layer = "controlled_runtime_integration_trial"

    required_freezes = [
        "TE-v3.2",
        "TE-v3.3",
        "TE-v3.4",
        "TE-v3.5",
        "TE-v3.6",
        "TE-v3.7",
    ]
    required_prechecks = [
        "RuntimeReadinessDecision",
        "RuntimeIntegrationFeatureFlag",
        "RuntimeOptInHookGuard",
        "RuntimeSafeHookPreflightGuard",
    ]
    allowed_trial_inputs = [
        "runtime_id",
        "chunk_metadata",
        "resume_plan",
        "scheduler_snapshot",
        "config",
        "env",
    ]
    forbidden_trial_inputs = ["source_text", "text", "chunks", "api_key", "provider_client"]
    expected_outputs = [
        "trial_status",
        "admission_decision",
        "rollback_status",
        "runtime_report",
        "metadata",
    ]

    def build_contract(self, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "trial_layer": self.trial_layer,
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "contract_only",
            "real_translation": False,
            "real_runtime_execution": False,
            "provider_access": "forbidden",
            "http_access": "forbidden",
            "api_key_access": "forbidden",
            "launcher_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "rollback_mode": "immediate_disable",
            "required_freezes": list(self.required_freezes),
            "required_prechecks": list(self.required_prechecks),
            "allowed_trial_inputs": list(self.allowed_trial_inputs),
            "forbidden_trial_inputs": list(self.forbidden_trial_inputs),
            "expected_outputs": list(self.expected_outputs),
            "safety_guarantees": {
                "disabled_by_default": True,
                "explicit_opt_in_required": True,
                "execution_allowed": False,
                "real_runtime_allowed": False,
                "provider_runtime_unchanged": True,
                "launcher_flow_unchanged": True,
                "translation_runtime_flow_unchanged": True,
            },
            "metadata": {
                "contract": "controlled_runtime_trial_contract",
                "stage": self.stage,
                "contract_only": True,
                **dict(metadata or {}),
            },
        }

    def validate_contract(self, contract: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(contract or {})
        errors: list[str] = []
        expected_values = {
            "version": self.version,
            "stage": self.stage,
            "trial_layer": self.trial_layer,
            "default_mode": "disabled",
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "contract_only",
            "real_translation": False,
            "real_runtime_execution": False,
            "provider_access": "forbidden",
            "http_access": "forbidden",
            "api_key_access": "forbidden",
            "launcher_touch_mode": "none",
            "translation_runtime_touch_mode": "none",
            "rollback_mode": "immediate_disable",
        }
        for key, expected in expected_values.items():
            if data.get(key) != expected:
                errors.append(f"{key} must be {str(expected).lower() if isinstance(expected, bool) else expected}")

        self._validate_required_items(data, "required_freezes", self.required_freezes, errors)
        self._validate_required_items(data, "required_prechecks", self.required_prechecks, errors)
        self._validate_required_items(data, "allowed_trial_inputs", self.allowed_trial_inputs, errors)
        self._validate_required_items(data, "forbidden_trial_inputs", self.forbidden_trial_inputs, errors)
        self._validate_required_items(data, "expected_outputs", self.expected_outputs, errors)

        guarantees = data.get("safety_guarantees")
        if not isinstance(guarantees, Mapping):
            errors.append("safety_guarantees mapping is required")
        else:
            required_guarantees = {
                "disabled_by_default": True,
                "explicit_opt_in_required": True,
                "execution_allowed": False,
                "real_runtime_allowed": False,
                "provider_runtime_unchanged": True,
                "launcher_flow_unchanged": True,
                "translation_runtime_flow_unchanged": True,
            }
            for key, expected in required_guarantees.items():
                if guarantees.get(key) is not expected:
                    errors.append(f"safety_guarantees.{key} must be {str(expected).lower()}")

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")
        return {"valid": not errors, "errors": errors}

    def describe_trial(self) -> dict[str, Any]:
        contract = self.build_contract()
        guarantees = contract["safety_guarantees"]
        return {
            "current_stage": contract["stage"],
            "current_mode": contract["execution_mode"],
            "execution_allowed": guarantees["execution_allowed"],
            "real_runtime_allowed": guarantees["real_runtime_allowed"],
            "rollback_available": contract["rollback_mode"] == "immediate_disable",
            "provider_connected": False,
            "launcher_modified": False,
            "translation_runtime_modified": False,
        }

    def _validate_required_items(
        self, data: Mapping[str, Any], key: str, required: list[str], errors: list[str]
    ) -> None:
        values = data.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            errors.append(f"{key} list is required")
            return
        for item in required:
            if item not in values:
                errors.append(f"{key} missing {item}")


__all__ = ["ControlledRuntimeTrialContract"]
