"""Service policy models for NTPE 1.0 Beta Stage-10.7.

The policy layer is an additive Platform Services component. It provides a
small, dependency-free policy decision model without mutating frozen
Foundation, CLI, SDK, Integration, or Workflow behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

PLATFORM_POLICY_VERSION = "1.0.0-beta.10.7"
PLATFORM_POLICY_STAGE = "10.7"

PolicyRule = Callable[["PlatformPolicyContext"], bool]


class PlatformPolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class PlatformPolicyContext:
    service_name: str
    action: str
    subject: Optional[str] = None
    resource: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.service_name or not str(self.service_name).strip():
            raise ValueError("policy context service_name is required")
        if not self.action or not str(self.action).strip():
            raise ValueError("policy context action is required")
        object.__setattr__(self, "service_name", str(self.service_name))
        object.__setattr__(self, "action", str(self.action))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.subject is not None:
            object.__setattr__(self, "subject", str(self.subject))
        if self.resource is not None:
            object.__setattr__(self, "resource", str(self.resource))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "action": self.action,
            "subject": self.subject,
            "resource": self.resource,
            "metadata": dict(self.metadata),
        }


@dataclass
class PlatformPolicy:
    name: str
    decision: PlatformPolicyDecision | str = PlatformPolicyDecision.ALLOW
    rule: Optional[PolicyRule] = None
    priority: int = 100
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    policy_id: str = field(default_factory=lambda: f"platform-policy-{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ValueError("policy name is required")
        self.name = str(self.name)
        if not isinstance(self.decision, PlatformPolicyDecision):
            self.decision = PlatformPolicyDecision(str(self.decision))
        if self.rule is not None and not callable(self.rule):
            raise TypeError("policy rule must be callable")
        self.priority = int(self.priority)
        self.description = str(self.description or "")
        self.metadata = dict(self.metadata or {})

    def applies(self, context: PlatformPolicyContext) -> bool:
        if not self.active:
            return False
        if self.rule is None:
            return True
        return bool(self.rule(context))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "decision": self.decision.value,
            "priority": self.priority,
            "description": self.description,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PlatformPolicyEvaluation:
    context: PlatformPolicyContext
    decision: PlatformPolicyDecision
    allowed: bool
    policy_name: Optional[str] = None
    policy_id: Optional[str] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "decision": self.decision.value,
            "allowed": self.allowed,
            "policy_name": self.policy_name,
            "policy_id": self.policy_id,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "evaluated_at": self.evaluated_at,
        }
