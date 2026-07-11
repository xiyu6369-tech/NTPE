from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeReadinessGateEvaluator:
    """Evaluate supplied readiness evidence without touching runtime systems."""

    stage = "3.7.2"

    def evaluate(
        self,
        contract: Mapping[str, Any] | None = None,
        state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract_data = dict(contract or {})
        state_data = dict(state or {})
        freezes = self._mapping(state_data.get("freezes"))
        checks = self._mapping(state_data.get("checks"))
        required_freezes = self._items(contract_data.get("required_freezes"))
        required_checks = self._items(contract_data.get("readiness_checks"))

        missing_freezes = [name for name in required_freezes if freezes.get(name) is not True]
        missing_checks = [name for name in required_checks if checks.get(name) is not True]
        unsafe_conditions: list[str] = []

        if not contract_data:
            unsafe_conditions.append("contract_missing")
        if not state_data:
            unsafe_conditions.append("state_missing")
        if contract_data.get("default_mode") != "disabled":
            unsafe_conditions.append("default_mode_not_disabled")
        if contract_data.get("enabled_mode") != "mock_only":
            unsafe_conditions.append("enabled_mode_not_mock_only")
        for key in ("runtime_touch_mode", "launcher_touch_mode", "provider_touch_mode"):
            if contract_data.get(key) != "none":
                unsafe_conditions.append(f"{key}_not_none")
        if contract_data.get("real_translation") is not False:
            unsafe_conditions.append("real_translation_not_false")

        evaluated_mode = state_data.get("mode", "disabled")
        if evaluated_mode != "mock_only":
            unsafe_conditions.append("state_mode_not_mock_only")

        ready = not missing_freezes and not missing_checks and not unsafe_conditions
        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "stage": self.stage,
            "missing_freezes": missing_freezes,
            "missing_checks": missing_checks,
            "unsafe_conditions": unsafe_conditions,
            "evaluated_mode": evaluated_mode,
            "next_allowed_mode": "mock_only",
            "real_runtime_allowed": False,
            "metadata": {
                "evaluator": "runtime_readiness_gate_evaluator",
                "stage": self.stage,
                "state_source": "supplied_mapping",
                "runtime_touch_mode": "none",
            },
        }

    def is_ready(self, report: Mapping[str, Any] | None) -> bool:
        return bool(report and report.get("ready") is True and report.get("status") == "ready")

    def validate_report(self, report: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(report or {})
        errors: list[str] = []
        required = {
            "ready", "status", "stage", "missing_freezes", "missing_checks",
            "unsafe_conditions", "evaluated_mode", "next_allowed_mode",
            "real_runtime_allowed", "metadata",
        }
        for key in sorted(required - data.keys()):
            errors.append(f"missing {key}")
        if data.get("real_runtime_allowed") is not False:
            errors.append("real_runtime_allowed must be false")
        if data.get("next_allowed_mode") != "mock_only":
            errors.append("next_allowed_mode must be mock_only")
        if data.get("status") not in {"ready", "not_ready"}:
            errors.append("status must be ready or not_ready")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.7.2")
        for key in ("missing_freezes", "missing_checks", "unsafe_conditions"):
            if not isinstance(data.get(key), list):
                errors.append(f"{key} list is required")
        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")
        if data.get("ready") is True:
            if data.get("status") != "ready":
                errors.append("ready report status must be ready")
            for key in ("missing_freezes", "missing_checks", "unsafe_conditions"):
                if data.get(key):
                    errors.append(f"ready report {key} must be empty")
        return {"valid": not errors, "errors": errors}

    @staticmethod
    def _mapping(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, Mapping) else {}

    @staticmethod
    def _items(value: Any) -> list[str]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return []
        return [item for item in value if isinstance(item, str)]


__all__ = ["RuntimeReadinessGateEvaluator"]
