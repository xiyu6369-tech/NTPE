from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeReadinessGateContract:
    """Contract for checking future Translation Runtime integration readiness."""

    version = "TE-v3.7"
    stage = "3.7.1"
    gate_layer = "runtime_readiness_gate"

    required_freezes = ["TE-v3.2", "TE-v3.3", "TE-v3.4", "TE-v3.5", "TE-v3.6"]
    required_readiness_checks = [
        "feature_flag_present",
        "disabled_guard_present",
        "optin_hook_present",
        "preflight_present",
        "boundary_regression_present",
    ]
    required_forbidden_side_effects = [
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "translation_runtime_flow",
        "real_translation",
    ]
    expected_outputs = ["readiness_status", "readiness_report", "missing_requirements", "metadata"]

    def build_contract(self, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "gate_layer": self.gate_layer,
            "default_mode": "disabled",
            "enabled_mode": "mock_only",
            "runtime_touch_mode": "none",
            "launcher_touch_mode": "none",
            "provider_touch_mode": "none",
            "real_translation": False,
            "required_freezes": list(self.required_freezes),
            "readiness_checks": list(self.required_readiness_checks),
            "forbidden_side_effects": list(self.required_forbidden_side_effects),
            "expected_outputs": list(self.expected_outputs),
            "metadata": {
                "contract": "runtime_readiness_gate_contract",
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
            errors.append("version must be TE-v3.7")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.7.1")
        if data.get("gate_layer") != self.gate_layer:
            errors.append("gate_layer must be runtime_readiness_gate")
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

        self._validate_required_items(data, "required_freezes", self.required_freezes, errors)
        self._validate_required_items(data, "readiness_checks", self.required_readiness_checks, errors)
        self._validate_required_items(data, "forbidden_side_effects", self.required_forbidden_side_effects, errors)
        self._validate_required_items(data, "expected_outputs", self.expected_outputs, errors)

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def describe_gate(self) -> dict[str, Any]:
        contract = self.build_contract()
        return {
            "gate_layer": contract["gate_layer"],
            "stage": contract["stage"],
            "default_mode": contract["default_mode"],
            "enabled_mode": contract["enabled_mode"],
            "runtime_touch_mode": contract["runtime_touch_mode"],
            "launcher_touch_mode": contract["launcher_touch_mode"],
            "provider_touch_mode": contract["provider_touch_mode"],
            "real_translation": contract["real_translation"],
            "required_freezes": list(contract["required_freezes"]),
            "readiness_checks": list(contract["readiness_checks"]),
            "summary": "Runtime readiness gate contract; no runtime, launcher, provider, or real translation touch.",
        }

    def _validate_required_items(self, data: Mapping[str, Any], key: str, required: list[str], errors: list[str]) -> None:
        values = data.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            errors.append(f"{key} list is required")
            return
        missing = [item for item in required if item not in values]
        for item in missing:
            errors.append(f"{key} missing {item}")


__all__ = ["RuntimeReadinessGateContract"]
