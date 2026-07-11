from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .runtime_disabled_trial_mock_bridge import RuntimeDisabledTrialMockBridge
from .runtime_integration_feature_flag import RuntimeIntegrationFeatureFlag
from .runtime_safe_hook_preflight_contract import RuntimeSafeHookPreflightContract
from .runtime_safe_hook_preflight_guard import RuntimeSafeHookPreflightGuard


class RuntimeSafeHookPreflightMockBridge:
    """Mock bridge for safe runtime adapter hook preflight trials."""

    stage = "3.6.3"

    def __init__(
        self,
        contract_builder: RuntimeSafeHookPreflightContract | None = None,
        feature_flag: RuntimeIntegrationFeatureFlag | None = None,
        preflight_guard: RuntimeSafeHookPreflightGuard | None = None,
        disabled_trial_bridge: RuntimeDisabledTrialMockBridge | None = None,
    ) -> None:
        self.contract_builder = contract_builder or RuntimeSafeHookPreflightContract()
        self.feature_flag = feature_flag or RuntimeIntegrationFeatureFlag()
        self.preflight_guard = preflight_guard or RuntimeSafeHookPreflightGuard(self.contract_builder)
        self.disabled_trial_bridge = disabled_trial_bridge or RuntimeDisabledTrialMockBridge()

    def run(
        self,
        request: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        env: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = self.contract_builder.build_contract(metadata={"bridge_stage": self.stage})
        flag_state = self.feature_flag.resolve(config=config, env=env)
        preflight_guard_result = self.preflight_guard.guard(
            request=request,
            contract=contract,
            flag_state=flag_state,
        )

        if preflight_guard_result["blocked"]:
            return self._result(
                status="preflight_blocked",
                preflight_guard_result=preflight_guard_result,
                disabled_trial_result={},
                preflight_status={"mode": "blocked", "executed": False, "reason": preflight_guard_result["reason"]},
                trial_status={"mode": "blocked", "executed": False, "reason": preflight_guard_result["reason"]},
                integration_status={"mode": "blocked", "executed": False, "reason": preflight_guard_result["reason"]},
                runtime_report={},
                export_outputs={},
            )

        trial_request = self._trial_request(request or {})
        disabled_trial_result = self.disabled_trial_bridge.run(
            request=trial_request,
            config={"runtime_scheduler_integration_enabled": True},
        )
        return self._result(
            status="preflight_mock_completed",
            preflight_guard_result=preflight_guard_result,
            disabled_trial_result=disabled_trial_result,
            preflight_status={"mode": "mock", "executed": False, "reason": "preflight_mock_completed"},
            trial_status=dict(disabled_trial_result.get("trial_status", {})),
            integration_status=dict(disabled_trial_result.get("integration_status", {})),
            runtime_report=dict(disabled_trial_result.get("runtime_report", {})),
            export_outputs=dict(disabled_trial_result.get("export_outputs", {})),
        )

    def validate_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []

        if data.get("status") not in {"preflight_blocked", "preflight_mock_completed"}:
            errors.append("status must be preflight_blocked or preflight_mock_completed")
        if not isinstance(data.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(data.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if data.get("allowed") == data.get("blocked"):
            errors.append("allowed and blocked must be opposites")

        for key in (
            "preflight_guard_result",
            "disabled_trial_result",
            "preflight_status",
            "trial_status",
            "integration_status",
            "runtime_report",
            "export_outputs",
            "metadata",
        ):
            if not isinstance(data.get(key), Mapping):
                errors.append(f"{key} mapping is required")

        if isinstance(data.get("preflight_guard_result"), Mapping):
            guard_validation = self.preflight_guard.validate_guard_result(data["preflight_guard_result"])
            if not guard_validation["valid"]:
                errors.extend(f"preflight_guard_result: {error}" for error in guard_validation["errors"])

        if data.get("status") == "preflight_blocked":
            if data.get("disabled_trial_result") != {}:
                errors.append("preflight_blocked must not include disabled_trial_result")
            if data.get("runtime_report") != {}:
                errors.append("preflight_blocked runtime_report must be empty")
            if data.get("export_outputs") != {}:
                errors.append("preflight_blocked export_outputs must be empty")

        if data.get("status") == "preflight_mock_completed":
            disabled_trial_result = data.get("disabled_trial_result", {})
            if disabled_trial_result.get("status") != "trial_mock_completed":
                errors.append("disabled_trial_result must be trial_mock_completed")
            if data.get("integration_status", {}).get("mode") != "mock":
                errors.append("integration_status mode must be mock")
            if data.get("integration_status", {}).get("executed") is not False:
                errors.append("integration_status executed must be false")
            if data.get("integration_status", {}).get("real_translation") is not False:
                errors.append("real_translation must be false")

        return {"valid": not errors, "errors": errors}

    def _trial_request(self, request: Mapping[str, Any]) -> dict[str, Any]:
        forwarded = dict(request)
        forwarded["request_type"] = str(request.get("request_type", request.get("type", "safe_hook_preflight")))
        return forwarded

    def _result(
        self,
        status: str,
        preflight_guard_result: Mapping[str, Any],
        disabled_trial_result: Mapping[str, Any],
        preflight_status: Mapping[str, Any],
        trial_status: Mapping[str, Any],
        integration_status: Mapping[str, Any],
        runtime_report: Mapping[str, Any],
        export_outputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "allowed": bool(preflight_guard_result["allowed"]),
            "blocked": bool(preflight_guard_result["blocked"]),
            "preflight_guard_result": dict(preflight_guard_result),
            "disabled_trial_result": dict(disabled_trial_result),
            "preflight_status": dict(preflight_status),
            "trial_status": dict(trial_status),
            "integration_status": dict(integration_status),
            "runtime_report": dict(runtime_report),
            "export_outputs": dict(export_outputs),
            "metadata": {
                "bridge": "runtime_safe_hook_preflight_mock_bridge",
                "stage": self.stage,
                "real_translation": False,
            },
        }


__all__ = ["RuntimeSafeHookPreflightMockBridge"]
