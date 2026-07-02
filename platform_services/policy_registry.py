"""Policy registry for NTPE 1.0 Beta Stage-10.7."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .service_policy import PLATFORM_POLICY_STAGE, PLATFORM_POLICY_VERSION, PlatformPolicy, PlatformPolicyDecision, PolicyRule


class PlatformPolicyRegistry:
    """In-memory registry for ordered service policies."""

    version = PLATFORM_POLICY_VERSION
    stage = PLATFORM_POLICY_STAGE

    def __init__(self, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.metadata = dict(metadata or {})
        self._policies: Dict[str, PlatformPolicy] = {}

    def register(
        self,
        name: str,
        *,
        decision: PlatformPolicyDecision | str = PlatformPolicyDecision.ALLOW,
        rule: Optional[PolicyRule] = None,
        priority: int = 100,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PlatformPolicy:
        policy = PlatformPolicy(
            name=name,
            decision=decision,
            rule=rule,
            priority=priority,
            description=description,
            metadata=dict(metadata or {}),
        )
        self._policies[policy.policy_id] = policy
        return policy

    def unregister(self, policy_id: str) -> bool:
        policy = self._policies.get(str(policy_id))
        if policy is None:
            return False
        policy.active = False
        return True

    def get(self, policy_id: str) -> Optional[PlatformPolicy]:
        return self._policies.get(str(policy_id))

    def policies(self, *, active_only: bool = False) -> tuple[PlatformPolicy, ...]:
        values: Iterable[PlatformPolicy] = self._policies.values()
        if active_only:
            values = [policy for policy in values if policy.active]
        return tuple(sorted(values, key=lambda item: (item.priority, item.name, item.policy_id)))

    def summary(self) -> Dict[str, Any]:
        active = [policy for policy in self._policies.values() if policy.active]
        return {
            "version": self.version,
            "stage": self.stage,
            "policy_count": len(self._policies),
            "active_policy_count": len(active),
            "allow_policy_count": sum(1 for policy in active if policy.decision == PlatformPolicyDecision.ALLOW),
            "deny_policy_count": sum(1 for policy in active if policy.decision == PlatformPolicyDecision.DENY),
            "metadata": dict(self.metadata),
        }

    def manifest(self) -> Dict[str, Any]:
        payload = self.summary()
        payload.update(
            {
                "policies": [policy.to_dict() for policy in self.policies()],
                "foundation_status": "frozen",
                "cli_status": "frozen",
                "sdk_status": "complete",
                "integration_status": "frozen",
                "workflow_status": "frozen",
                "additive_only": True,
            }
        )
        return payload
