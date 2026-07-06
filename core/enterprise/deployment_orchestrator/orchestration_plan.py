from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseOrchestrationPlan:
    """Additive deployment orchestration plan.

    Stage-18.5 coordinates Stage-18.2 configuration, Stage-18.3 profiles, and
    Stage-18.4 runtime readiness without mutating frozen foundation or LTS code.
    """

    stage: str
    profile: str
    environment: str
    target: str
    mode: str = "additive"
    phases: List[str] = field(default_factory=list)
    gates: List[str] = field(default_factory=list)
    rollback: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_runtime_payload(cls, runtime_payload: Dict[str, Any]) -> "EnterpriseOrchestrationPlan":
        context = dict(runtime_payload.get("context", {}))
        plan = dict(runtime_payload.get("plan", {}))
        phases = [
            "configuration_resolution",
            "profile_resolution",
            "runtime_preparation",
            "compatibility_gate",
            "deployment_readiness_gate",
            "audit_materialization",
        ]
        if "prepare_rollback_checkpoint" in plan.get("steps", []):
            phases.append("rollback_checkpoint")
        return cls(
            stage="Stage-18.5",
            profile=str(context.get("profile", "local-workstation")),
            environment=str(context.get("environment", "development")),
            target=str(context.get("target", "local-workstation")),
            phases=phases,
            gates=[
                "runtime_success",
                "additive_mode",
                "compatibility_contract",
                "rollback_available",
            ],
            rollback=[
                "stop_orchestration",
                "discard_orchestration_plan",
                "restore_stage18_runtime_context",
                "re_run_ntpe_validation",
            ],
            metadata={
                "runtime_stage": runtime_payload.get("stage"),
                "runtime_success": bool(runtime_payload.get("success")),
                "phase_count": len(phases),
                "compatibility": "orchestrator-additive-only",
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "profile": self.profile,
            "environment": self.environment,
            "target": self.target,
            "mode": self.mode,
            "phases": list(self.phases),
            "gates": list(self.gates),
            "rollback": list(self.rollback),
            "metadata": dict(self.metadata),
        }
