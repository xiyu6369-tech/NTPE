"""Service policy engine for NTPE 1.0 Beta Stage-10.7."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .platform_events import PLATFORM_EVENTS
from .policy_registry import PlatformPolicyRegistry
from .service_policy import (
    PLATFORM_POLICY_STAGE,
    PLATFORM_POLICY_VERSION,
    PlatformPolicyContext,
    PlatformPolicyDecision,
    PlatformPolicyEvaluation,
)


class PlatformPolicyEngine:
    """Evaluates ordered service policies and returns allow/deny decisions."""

    version = PLATFORM_POLICY_VERSION
    stage = PLATFORM_POLICY_STAGE

    def __init__(
        self,
        *,
        registry: Optional[PlatformPolicyRegistry] = None,
        default_decision: PlatformPolicyDecision | str = PlatformPolicyDecision.ALLOW,
        event_bus: Any = None,
        metrics: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.registry = registry or PlatformPolicyRegistry()
        self.default_decision = default_decision if isinstance(default_decision, PlatformPolicyDecision) else PlatformPolicyDecision(str(default_decision))
        self.event_bus = event_bus
        self.metrics = metrics
        self.metadata = dict(metadata or {})
        self.history: list[PlatformPolicyEvaluation] = []

    def allow(self, name: str, rule=None, *, priority: int = 100, description: str = "", metadata: Optional[Dict[str, Any]] = None):
        return self.registry.register(name, decision=PlatformPolicyDecision.ALLOW, rule=rule, priority=priority, description=description, metadata=metadata)

    def deny(self, name: str, rule=None, *, priority: int = 100, description: str = "", metadata: Optional[Dict[str, Any]] = None):
        return self.registry.register(name, decision=PlatformPolicyDecision.DENY, rule=rule, priority=priority, description=description, metadata=metadata)

    def evaluate(self, context: PlatformPolicyContext | Dict[str, Any], **kwargs: Any) -> PlatformPolicyEvaluation:
        if isinstance(context, PlatformPolicyContext):
            policy_context = context
        elif isinstance(context, dict):
            policy_context = PlatformPolicyContext(**context)
        else:
            policy_context = PlatformPolicyContext(context, kwargs.pop("action"), **kwargs)

        for policy in self.registry.policies(active_only=True):
            if policy.applies(policy_context):
                evaluation = PlatformPolicyEvaluation(
                    context=policy_context,
                    decision=policy.decision,
                    allowed=policy.decision == PlatformPolicyDecision.ALLOW,
                    policy_name=policy.name,
                    policy_id=policy.policy_id,
                    reason=f"matched policy: {policy.name}",
                    metadata={"priority": policy.priority, **dict(policy.metadata)},
                )
                return self._record(evaluation)

        evaluation = PlatformPolicyEvaluation(
            context=policy_context,
            decision=self.default_decision,
            allowed=self.default_decision == PlatformPolicyDecision.ALLOW,
            reason="default policy",
            metadata={"default": True},
        )
        return self._record(evaluation)

    def can(self, service_name: str, action: str, **kwargs: Any) -> bool:
        return self.evaluate(PlatformPolicyContext(service_name=service_name, action=action, **kwargs)).allowed

    def require(self, service_name: str, action: str, **kwargs: Any) -> PlatformPolicyEvaluation:
        evaluation = self.evaluate(PlatformPolicyContext(service_name=service_name, action=action, **kwargs))
        if not evaluation.allowed:
            raise PermissionError(f"policy denied {service_name}:{action}: {evaluation.reason}")
        return evaluation

    def _record(self, evaluation: PlatformPolicyEvaluation) -> PlatformPolicyEvaluation:
        self.history.append(evaluation)
        if self.metrics is not None and hasattr(self.metrics, "counter"):
            self.metrics.counter("platform.policy.evaluations", 1, metadata={"decision": evaluation.decision.value})
            self.metrics.counter(f"platform.policy.{evaluation.decision.value}", 1, metadata={"service": evaluation.context.service_name})
        if self.event_bus is not None and hasattr(self.event_bus, "publish"):
            self.event_bus.publish(
                PLATFORM_EVENTS.get("policy_evaluated", "platform.policy.evaluated"),
                evaluation.to_dict(),
                source="platform.policy",
                topic="policy",
            )
        return evaluation

    def summary(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "evaluation_count": len(self.history),
            "allowed_count": sum(1 for item in self.history if item.allowed),
            "denied_count": sum(1 for item in self.history if not item.allowed),
            "default_decision": self.default_decision.value,
            "registry": self.registry.summary(),
            "metadata": dict(self.metadata),
        }

    def manifest(self) -> Dict[str, Any]:
        payload = self.summary()
        payload.update(
            {
                "foundation_status": "frozen",
                "cli_status": "frozen",
                "sdk_status": "complete",
                "integration_status": "frozen",
                "workflow_status": "frozen",
                "additive_only": True,
                "future_rbac_abac_ready": True,
            }
        )
        return payload


def create_policy_engine(**kwargs: Any) -> PlatformPolicyEngine:
    return PlatformPolicyEngine(**kwargs)
