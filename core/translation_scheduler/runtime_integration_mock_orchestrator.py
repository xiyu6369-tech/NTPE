from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .runtime_integration_contract import RuntimeIntegrationContract
from .runtime_integration_feature_flag import RuntimeIntegrationFeatureFlag
from .runtime_integration_guard import RuntimeIntegrationDisabledGuard


class RuntimeIntegrationMockOrchestrator:
    """Mock-only orchestrator for the runtime integration planning path."""

    stage = "3.3.4"

    def __init__(
        self,
        contract_builder: RuntimeIntegrationContract | None = None,
        feature_flag: RuntimeIntegrationFeatureFlag | None = None,
        guard: RuntimeIntegrationDisabledGuard | None = None,
    ) -> None:
        self.contract_builder = contract_builder or RuntimeIntegrationContract()
        self.feature_flag = feature_flag or RuntimeIntegrationFeatureFlag()
        self.guard = guard or RuntimeIntegrationDisabledGuard()

    def run(
        self,
        request: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        env: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract = self.contract_builder.build_contract(metadata={"orchestrator_stage": self.stage})
        flag_state = self.feature_flag.resolve(config=config, env=env)
        guard_result = self.guard.guard(flag_state, request=request)

        if guard_result["blocked"]:
            return self._result(
                status="blocked",
                contract=contract,
                flag_state=flag_state,
                guard_result=guard_result,
                runtime_report={},
                export_outputs={},
                integration_status={
                    "mode": "blocked",
                    "executed": False,
                    "reason": guard_result["reason"],
                },
            )

        request_summary = guard_result["request_summary"]
        return self._result(
            status="mock_completed",
            contract=contract,
            flag_state=flag_state,
            guard_result=guard_result,
            runtime_report={
                "mode": "mock",
                "jobs_total": request_summary["chunk_count"],
                "jobs_done": request_summary["chunk_count"],
                "jobs_failed": 0,
                "provider_runtime": "not_connected",
            },
            export_outputs={
                "mode": "mock",
                "merged_text": "",
                "chunk_results": [],
                "failed_chunks": [],
                "manifest": {
                    "chunks_total": request_summary["chunk_count"],
                    "merge_ready": True,
                    "mock": True,
                },
            },
            integration_status={
                "mode": "mock",
                "executed": False,
                "provider_runtime": "not_connected",
                "real_translation": False,
            },
        )

    def validate_result(self, result: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(result or {})
        errors: list[str] = []

        if data.get("status") not in {"blocked", "mock_completed"}:
            errors.append("status must be blocked or mock_completed")
        if not isinstance(data.get("allowed"), bool):
            errors.append("allowed boolean is required")
        if not isinstance(data.get("blocked"), bool):
            errors.append("blocked boolean is required")
        if data.get("allowed") == data.get("blocked"):
            errors.append("allowed and blocked must be opposites")
        for key in ("contract", "flag_state", "guard_result", "runtime_report", "export_outputs", "integration_status", "metadata"):
            if not isinstance(data.get(key), Mapping):
                errors.append(f"{key} mapping is required")

        if isinstance(data.get("guard_result"), Mapping):
            guard_validation = self.guard.validate_guard_result(data["guard_result"])
            if not guard_validation["valid"]:
                errors.extend(f"guard_result: {error}" for error in guard_validation["errors"])

        if isinstance(data.get("integration_status"), Mapping):
            mode = data["integration_status"].get("mode")
            if data.get("status") == "mock_completed" and mode != "mock":
                errors.append("mock_completed integration_status mode must be mock")
            if data.get("status") == "blocked" and mode != "blocked":
                errors.append("blocked integration_status mode must be blocked")

        return {"valid": not errors, "errors": errors}

    def _result(
        self,
        status: str,
        contract: Mapping[str, Any],
        flag_state: Mapping[str, Any],
        guard_result: Mapping[str, Any],
        runtime_report: Mapping[str, Any],
        export_outputs: Mapping[str, Any],
        integration_status: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "allowed": bool(guard_result["allowed"]),
            "blocked": bool(guard_result["blocked"]),
            "contract": dict(contract),
            "flag_state": dict(flag_state),
            "guard_result": dict(guard_result),
            "runtime_report": dict(runtime_report),
            "export_outputs": dict(export_outputs),
            "integration_status": dict(integration_status),
            "metadata": {
                "orchestrator": "runtime_integration_mock_orchestrator",
                "stage": self.stage,
                "real_translation": False,
            },
        }


__all__ = ["RuntimeIntegrationMockOrchestrator"]
