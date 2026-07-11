from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeOptInHookContract:
    """Contract for a future optional Translation Runtime adapter hook."""

    version = "TE-v3.4"
    stage = "3.4.1"
    hook_layer = "runtime_optin_adapter_hook"

    required_forbidden_side_effects = [
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "real_translation",
    ]
    required_prechecks = [
        "RuntimeIntegrationFeatureFlag",
        "RuntimeIntegrationDisabledGuard",
        "RuntimeIntegrationMockOrchestrator",
    ]

    def build_contract(self, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "hook_layer": self.hook_layer,
            "enabled_by_default": False,
            "activation_mode": "explicit_opt_in_only",
            "execution_mode": "mock_only",
            "allowed_callers": ["translation_runtime"],
            "forbidden_side_effects": list(self.required_forbidden_side_effects),
            "required_prechecks": list(self.required_prechecks),
            "expected_hook_inputs": [
                "runtime_state",
                "resume_plan",
                "config",
                "env",
            ],
            "expected_hook_outputs": [
                "hook_status",
                "integration_status",
                "runtime_report",
                "export_outputs",
            ],
            "metadata": {
                "contract": "runtime_optin_hook_contract",
                "stage": self.stage,
                "disabled_by_default": True,
                "real_translation": False,
                **dict(metadata or {}),
            },
        }

    def validate_contract(self, contract: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(contract or {})
        errors: list[str] = []

        if data.get("version") != self.version:
            errors.append("version must be TE-v3.4")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.4.1")
        if data.get("hook_layer") != self.hook_layer:
            errors.append("hook_layer must be runtime_optin_adapter_hook")
        if data.get("enabled_by_default") is not False:
            errors.append("enabled_by_default must be false")
        if data.get("activation_mode") != "explicit_opt_in_only":
            errors.append("activation_mode must be explicit_opt_in_only")
        if data.get("execution_mode") != "mock_only":
            errors.append("execution_mode must be mock_only")

        self._validate_required_items(data, "allowed_callers", ["translation_runtime"], errors)
        self._validate_required_items(data, "forbidden_side_effects", self.required_forbidden_side_effects, errors)
        self._validate_required_items(data, "required_prechecks", self.required_prechecks, errors)
        self._validate_required_items(data, "expected_hook_inputs", ["runtime_state", "resume_plan", "config", "env"], errors)
        self._validate_required_items(
            data,
            "expected_hook_outputs",
            ["hook_status", "integration_status", "runtime_report", "export_outputs"],
            errors,
        )

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def describe_hook(self) -> dict[str, Any]:
        contract = self.build_contract()
        return {
            "hook_layer": contract["hook_layer"],
            "stage": contract["stage"],
            "enabled_by_default": contract["enabled_by_default"],
            "activation_mode": contract["activation_mode"],
            "execution_mode": contract["execution_mode"],
            "allowed_callers": list(contract["allowed_callers"]),
            "required_prechecks": list(contract["required_prechecks"]),
            "summary": "Optional future Translation Runtime hook; disabled by default and mock-only.",
        }

    def _validate_required_items(self, data: Mapping[str, Any], key: str, required: list[str], errors: list[str]) -> None:
        values = data.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            errors.append(f"{key} list is required")
            return
        missing = [item for item in required if item not in values]
        for item in missing:
            errors.append(f"{key} missing {item}")


__all__ = ["RuntimeOptInHookContract"]
