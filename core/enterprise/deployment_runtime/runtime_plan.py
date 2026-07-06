from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .runtime_context import EnterpriseRuntimeContext


@dataclass(frozen=True)
class EnterpriseRuntimePlan:
    stage: str
    profile: str
    environment: str
    target: str
    execution_mode: str = "additive"
    steps: List[str] = field(default_factory=list)
    rollback_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_context(cls, context: EnterpriseRuntimeContext) -> "EnterpriseRuntimePlan":
        steps = [
            "load_enterprise_configuration",
            "resolve_deployment_profile",
            "validate_runtime_context",
            "prepare_runtime_workspace",
            "attach_runtime_capabilities",
            "verify_backward_compatibility",
        ]
        if "audit_export" in context.capabilities:
            steps.append("prepare_audit_export")
        if "rollback_plan" in context.capabilities:
            steps.append("prepare_rollback_checkpoint")
        return cls(
            stage="Stage-18.4",
            profile=context.profile,
            environment=context.environment,
            target=context.target,
            steps=steps,
            rollback_steps=[
                "detach_runtime_capabilities",
                "restore_previous_enterprise_config",
                "re_run_ntpe_validation",
            ],
            metadata={
                "capability_count": len(context.capabilities),
                "compatibility": "additive-runtime-only",
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "profile": self.profile,
            "environment": self.environment,
            "target": self.target,
            "execution_mode": self.execution_mode,
            "steps": list(self.steps),
            "rollback_steps": list(self.rollback_steps),
            "metadata": dict(self.metadata),
        }
