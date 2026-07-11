from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeSafeHookPreflightContract:
    """Contract for safe runtime adapter hook preflight checks."""

    version = "TE-v3.6"
    stage = "3.6.1"
    preflight_layer = "runtime_safe_adapter_hook_preflight"

    required_frozen_layers = [
        "TE-v3.2 runtime_scheduler_adapter",
        "TE-v3.3 runtime_integration_planning",
        "TE-v3.4 runtime_optin_hook",
        "TE-v3.5 runtime_disabled_trial",
    ]
    required_prechecks = [
        "RuntimeIntegrationFeatureFlag",
        "RuntimeOptInHookGuard",
        "RuntimeDisabledTrialGuard",
        "RuntimeDisabledTrialMockBridge",
    ]
    required_forbidden_side_effects = [
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "translation_runtime_flow",
        "real_translation",
    ]

    def build_contract(self, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "preflight_layer": self.preflight_layer,
            "default_mode": "disabled",
            "enabled_mode": "mock_only",
            "runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "provider_touch_mode": "none",
            "real_translation": False,
            "required_frozen_layers": list(self.required_frozen_layers),
            "required_prechecks": list(self.required_prechecks),
            "expected_preflight_inputs": [
                "runtime_state",
                "resume_plan",
                "config",
                "env",
            ],
            "expected_preflight_outputs": [
                "preflight_status",
                "trial_status",
                "hook_status",
                "integration_status",
                "runtime_report",
                "export_outputs",
            ],
            "forbidden_side_effects": list(self.required_forbidden_side_effects),
            "metadata": {
                "contract": "runtime_safe_hook_preflight_contract",
                "stage": self.stage,
                "disabled_by_default": True,
                "mock_only": True,
                "runtime_touch_mode": "none",
                **dict(metadata or {}),
            },
        }

    def validate_contract(self, contract: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(contract or {})
        errors: list[str] = []

        if data.get("version") != self.version:
            errors.append("version must be TE-v3.6")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.6.1")
        if data.get("preflight_layer") != self.preflight_layer:
            errors.append("preflight_layer must be runtime_safe_adapter_hook_preflight")
        if data.get("default_mode") != "disabled":
            errors.append("default_mode must be disabled")
        if data.get("enabled_mode") != "mock_only":
            errors.append("enabled_mode must be mock_only")
        if data.get("runtime_touch_mode") != "none":
            errors.append("runtime_touch_mode must be none")
        if data.get("launcher_touch_mode") != "none":
            errors.append("launcher_touch_mode must be none")
        if data.get("provider_touch_mode") != "none":
            errors.append("provider_touch_mode must be none")
        if data.get("real_translation") is not False:
            errors.append("real_translation must be false")

        self._validate_required_items(data, "required_frozen_layers", self.required_frozen_layers, errors)
        self._validate_required_items(data, "required_prechecks", self.required_prechecks, errors)
        self._validate_required_items(
            data,
            "expected_preflight_inputs",
            ["runtime_state", "resume_plan", "config", "env"],
            errors,
        )
        self._validate_required_items(
            data,
            "expected_preflight_outputs",
            [
                "preflight_status",
                "trial_status",
                "hook_status",
                "integration_status",
                "runtime_report",
                "export_outputs",
            ],
            errors,
        )
        self._validate_required_items(data, "forbidden_side_effects", self.required_forbidden_side_effects, errors)

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def describe_preflight(self) -> dict[str, Any]:
        contract = self.build_contract()
        return {
            "preflight_layer": contract["preflight_layer"],
            "stage": contract["stage"],
            "default_mode": contract["default_mode"],
            "enabled_mode": contract["enabled_mode"],
            "runtime_touch_mode": contract["runtime_touch_mode"],
            "launcher_touch_mode": contract["launcher_touch_mode"],
            "provider_touch_mode": contract["provider_touch_mode"],
            "real_translation": contract["real_translation"],
            "required_frozen_layers": list(contract["required_frozen_layers"]),
            "required_prechecks": list(contract["required_prechecks"]),
            "summary": "Safe adapter hook preflight contract; no runtime, launcher, provider, or real translation touch.",
        }

    def _validate_required_items(self, data: Mapping[str, Any], key: str, required: list[str], errors: list[str]) -> None:
        values = data.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            errors.append(f"{key} list is required")
            return
        missing = [item for item in required if item not in values]
        for item in missing:
            errors.append(f"{key} missing {item}")


__all__ = ["RuntimeSafeHookPreflightContract"]
