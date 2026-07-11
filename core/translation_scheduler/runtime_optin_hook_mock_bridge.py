from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .runtime_integration_feature_flag import RuntimeIntegrationFeatureFlag
from .runtime_integration_mock_orchestrator import RuntimeIntegrationMockOrchestrator
from .runtime_optin_hook_contract import RuntimeOptInHookContract
from .runtime_optin_hook_guard import RuntimeOptInHookGuard


class RuntimeOptInHookMockBridge:
    """Mock bridge for future Translation Runtime opt-in hook calls."""

    stage = "3.4.3"

    def __init__(
        self,
        contract_builder: RuntimeOptInHookContract | None = None,
        feature_flag: RuntimeIntegrationFeatureFlag | None = None,
        hook_guard: RuntimeOptInHookGuard | None = None,
        orchestrator: RuntimeIntegrationMockOrchestrator | None = None,
    ) -> None:
        self.contract_builder = contract_builder or RuntimeOptInHookContract()
        self.feature_flag = feature_flag or RuntimeIntegrationFeatureFlag()
        self.hook_guard = hook_guard or RuntimeOptInHookGuard(self.contract_builder)
        self.orchestrator = orchestrator or RuntimeIntegrationMockOrchestrator()

    def run(
        self,
        request: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        env: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = self.contract_builder.build_contract(metadata={"bridge_stage": self.stage})
        flag_state = self.feature_flag.resolve(config=config, env=env)
        hook_guard_result = self.hook_guard.guard(request=request, contract=contract, flag_state=flag_state)

        if hook_guard_result["blocked"]:
            return self._result(
                status="hook_blocked",
                hook_guard_result=hook_guard_result,
                orchestrator_result={},
                hook_status={"mode": "blocked", "executed": False, "reason": hook_guard_result["reason"]},
                integration_status={"mode": "blocked", "executed": False, "reason": hook_guard_result["reason"]},
                runtime_report={},
                export_outputs={},
            )

        orchestrator_result = self.orchestrator.run(
            request=request,
            config={"runtime_scheduler_integration_enabled": True},
        )
        return self._result(
            status="hook_mock_completed",
            hook_guard_result=hook_guard_result,
            orchestrator_result=orchestrator_result,
            hook_status={"mode": "mock", "executed": False, "reason": "hook_mock_completed"},
            integration_status=dict(orchestrator_result.get("integration_status", {})),
            runtime_report=dict(orchestrator_result.get("runtime_report", {})),
            export_outputs=dict(orchestrator_result.get("export_outputs", {})),
        )

    def validate_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []

        if data.get("status") not in {"hook_blocked", "hook_mock_completed"}:
            errors.append("status must be hook_blocked or hook_mock_completed")
        if not isinstance(data.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(data.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if data.get("allowed") == data.get("blocked"):
            errors.append("allowed and blocked must be opposites")
        for key in (
            "hook_guard_result",
            "orchestrator_result",
            "hook_status",
            "integration_status",
            "runtime_report",
            "export_outputs",
            "metadata",
        ):
            if not isinstance(data.get(key), Mapping):
                errors.append(f"{key} mapping is required")

        if isinstance(data.get("hook_guard_result"), Mapping):
            guard_validation = self.hook_guard.validate_guard_result(data["hook_guard_result"])
            if not guard_validation["valid"]:
                errors.extend(f"hook_guard_result: {error}" for error in guard_validation["errors"])

        if data.get("status") == "hook_blocked":
            if data.get("orchestrator_result") != {}:
                errors.append("hook_blocked must not include orchestrator_result")
            if data.get("runtime_report") != {}:
                errors.append("hook_blocked runtime_report must be empty")
            if data.get("export_outputs") != {}:
                errors.append("hook_blocked export_outputs must be empty")

        if data.get("status") == "hook_mock_completed":
            orchestrator_result = data.get("orchestrator_result", {})
            if orchestrator_result.get("status") != "mock_completed":
                errors.append("orchestrator_result must be mock_completed")
            if data.get("integration_status", {}).get("mode") != "mock":
                errors.append("integration_status mode must be mock")
            if data.get("integration_status", {}).get("executed") is not False:
                errors.append("integration_status executed must be false")
            if data.get("integration_status", {}).get("real_translation") is not False:
                errors.append("real_translation must be false")

        return {"valid": not errors, "errors": errors}

    def _result(
        self,
        status: str,
        hook_guard_result: Mapping[str, Any],
        orchestrator_result: Mapping[str, Any],
        hook_status: Mapping[str, Any],
        integration_status: Mapping[str, Any],
        runtime_report: Mapping[str, Any],
        export_outputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "allowed": bool(hook_guard_result["allowed"]),
            "blocked": bool(hook_guard_result["blocked"]),
            "hook_guard_result": dict(hook_guard_result),
            "orchestrator_result": dict(orchestrator_result),
            "hook_status": dict(hook_status),
            "integration_status": dict(integration_status),
            "runtime_report": dict(runtime_report),
            "export_outputs": dict(export_outputs),
            "metadata": {
                "bridge": "runtime_optin_hook_mock_bridge",
                "stage": self.stage,
                "real_translation": False,
            },
        }


__all__ = ["RuntimeOptInHookMockBridge"]
