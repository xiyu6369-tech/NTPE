from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeIntegrationContract:
    """Planning contract for future runtime scheduler integration."""

    version = "TE-v3.3"
    stage = "3.3.1"
    integration_layer = "runtime_scheduler_integration"

    def build_contract(self, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "integration_layer": self.integration_layer,
            "enabled": False,
            "default_mode": "disabled",
            "required_boundaries": {
                "provider_runtime": "external",
                "http_client": "forbidden",
                "api_key": "forbidden",
                "launcher_flow": "unchanged",
                "translation_runtime_flow": "unchanged",
            },
            "required_inputs": [
                "runtime_state",
                "scheduler_snapshot",
                "resume_plan",
            ],
            "expected_outputs": [
                "runtime_report",
                "export_outputs",
                "integration_status",
            ],
            "metadata": {
                "contract": "runtime_integration_contract",
                "stage": self.stage,
                "disabled_by_default": True,
                **dict(metadata or {}),
            },
        }

    def validate_contract(self, contract: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(contract or {})
        errors: list[str] = []

        if data.get("version") != self.version:
            errors.append("version must be TE-v3.3")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.3.1")
        if data.get("integration_layer") != self.integration_layer:
            errors.append("integration_layer must be runtime_scheduler_integration")
        if data.get("enabled") is not False:
            errors.append("enabled must be false")
        if data.get("default_mode") != "disabled":
            errors.append("default_mode must be disabled")

        boundaries = data.get("required_boundaries")
        if not isinstance(boundaries, Mapping):
            errors.append("required_boundaries mapping is required")
            boundaries = {}
        expected_boundaries = {
            "provider_runtime": "external",
            "http_client": "forbidden",
            "api_key": "forbidden",
            "launcher_flow": "unchanged",
            "translation_runtime_flow": "unchanged",
        }
        for key, expected in expected_boundaries.items():
            if boundaries.get(key) != expected:
                errors.append(f"{key} boundary must be {expected}")

        self._validate_required_items(data, "required_inputs", ["runtime_state", "scheduler_snapshot", "resume_plan"], errors)
        self._validate_required_items(data, "expected_outputs", ["runtime_report", "export_outputs", "integration_status"], errors)

        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def is_enabled(self, contract: Mapping[str, Any] | None) -> bool:
        data = dict(contract or {})
        return data.get("enabled") is True and data.get("default_mode") != "disabled"

    def _validate_required_items(self, data: Mapping[str, Any], key: str, required: list[str], errors: list[str]) -> None:
        values = data.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            errors.append(f"{key} list is required")
            return
        missing = [item for item in required if item not in values]
        for item in missing:
            errors.append(f"{key} missing {item}")


__all__ = ["RuntimeIntegrationContract"]
