from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .runtime_disabled_trial_contract import RuntimeDisabledTrialContract
from .runtime_disabled_trial_guard import RuntimeDisabledTrialGuard
from .runtime_integration_feature_flag import RuntimeIntegrationFeatureFlag
from .runtime_optin_hook_mock_bridge import RuntimeOptInHookMockBridge


class RuntimeDisabledTrialMockBridge:
    """Mock bridge for disabled runtime adapter hook integration trials."""

    stage = "3.5.3"

    def __init__(
        self,
        contract_builder: RuntimeDisabledTrialContract | None = None,
        feature_flag: RuntimeIntegrationFeatureFlag | None = None,
        trial_guard: RuntimeDisabledTrialGuard | None = None,
        hook_bridge: RuntimeOptInHookMockBridge | None = None,
    ) -> None:
        self.contract_builder = contract_builder or RuntimeDisabledTrialContract()
        self.feature_flag = feature_flag or RuntimeIntegrationFeatureFlag()
        self.trial_guard = trial_guard or RuntimeDisabledTrialGuard(self.contract_builder)
        self.hook_bridge = hook_bridge or RuntimeOptInHookMockBridge()

    def run(
        self,
        request: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        env: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = self.contract_builder.build_contract(metadata={"bridge_stage": self.stage})
        flag_state = self.feature_flag.resolve(config=config, env=env)
        trial_guard_result = self.trial_guard.guard(request=request, contract=contract, flag_state=flag_state)

        if trial_guard_result["blocked"]:
            return self._result(
                status="trial_blocked",
                trial_guard_result=trial_guard_result,
                hook_bridge_result={},
                trial_status={"mode": "blocked", "executed": False, "reason": trial_guard_result["reason"]},
                hook_status={"mode": "blocked", "executed": False, "reason": trial_guard_result["reason"]},
                integration_status={"mode": "blocked", "executed": False, "reason": trial_guard_result["reason"]},
                runtime_report={},
                export_outputs={},
            )

        hook_request = self._hook_request(request or {})
        hook_bridge_result = self.hook_bridge.run(
            request=hook_request,
            config={"runtime_scheduler_integration_enabled": True},
        )
        return self._result(
            status="trial_mock_completed",
            trial_guard_result=trial_guard_result,
            hook_bridge_result=hook_bridge_result,
            trial_status={"mode": "mock", "executed": False, "reason": "trial_mock_completed"},
            hook_status=dict(hook_bridge_result.get("hook_status", {})),
            integration_status=dict(hook_bridge_result.get("integration_status", {})),
            runtime_report=dict(hook_bridge_result.get("runtime_report", {})),
            export_outputs=dict(hook_bridge_result.get("export_outputs", {})),
        )

    def validate_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []

        if data.get("status") not in {"trial_blocked", "trial_mock_completed"}:
            errors.append("status must be trial_blocked or trial_mock_completed")
        if not isinstance(data.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(data.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if data.get("allowed") == data.get("blocked"):
            errors.append("allowed and blocked must be opposites")

        for key in (
            "trial_guard_result",
            "hook_bridge_result",
            "trial_status",
            "hook_status",
            "integration_status",
            "runtime_report",
            "export_outputs",
            "metadata",
        ):
            if not isinstance(data.get(key), Mapping):
                errors.append(f"{key} mapping is required")

        if isinstance(data.get("trial_guard_result"), Mapping):
            guard_validation = self.trial_guard.validate_guard_result(data["trial_guard_result"])
            if not guard_validation["valid"]:
                errors.extend(f"trial_guard_result: {error}" for error in guard_validation["errors"])

        if data.get("status") == "trial_blocked":
            if data.get("hook_bridge_result") != {}:
                errors.append("trial_blocked must not include hook_bridge_result")
            if data.get("runtime_report") != {}:
                errors.append("trial_blocked runtime_report must be empty")
            if data.get("export_outputs") != {}:
                errors.append("trial_blocked export_outputs must be empty")

        if data.get("status") == "trial_mock_completed":
            hook_bridge_result = data.get("hook_bridge_result", {})
            if hook_bridge_result.get("status") != "hook_mock_completed":
                errors.append("hook_bridge_result must be hook_mock_completed")
            if data.get("integration_status", {}).get("mode") != "mock":
                errors.append("integration_status mode must be mock")
            if data.get("integration_status", {}).get("executed") is not False:
                errors.append("integration_status executed must be false")
            if data.get("integration_status", {}).get("real_translation") is not False:
                errors.append("real_translation must be false")

        return {"valid": not errors, "errors": errors}

    def _hook_request(self, request: Mapping[str, Any]) -> dict[str, Any]:
        forwarded = dict(request)
        forwarded["caller"] = "translation_runtime"
        forwarded["request_type"] = str(request.get("request_type", request.get("type", "disabled_trial")))
        return forwarded

    def _result(
        self,
        status: str,
        trial_guard_result: Mapping[str, Any],
        hook_bridge_result: Mapping[str, Any],
        trial_status: Mapping[str, Any],
        hook_status: Mapping[str, Any],
        integration_status: Mapping[str, Any],
        runtime_report: Mapping[str, Any],
        export_outputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "allowed": bool(trial_guard_result["allowed"]),
            "blocked": bool(trial_guard_result["blocked"]),
            "trial_guard_result": dict(trial_guard_result),
            "hook_bridge_result": dict(hook_bridge_result),
            "trial_status": dict(trial_status),
            "hook_status": dict(hook_status),
            "integration_status": dict(integration_status),
            "runtime_report": dict(runtime_report),
            "export_outputs": dict(export_outputs),
            "metadata": {
                "bridge": "runtime_disabled_trial_mock_bridge",
                "stage": self.stage,
                "real_translation": False,
            },
        }


__all__ = ["RuntimeDisabledTrialMockBridge"]
