"""NTPE 1.0 Beta Stage-10.7 Service Policy Layer test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_POLICY_STAGE,
    PlatformEventBus,
    PlatformMetricsRegistry,
    PlatformPolicyContext,
    PlatformPolicyDecision,
    PlatformPolicyEngine,
    PlatformPolicyEvaluation,
    PlatformPolicyRegistry,
    create_event_bus,
    create_metrics_registry,
    create_policy_engine,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.7 Service Policy Layer Test")
    print("=" * 82)

    bus = create_event_bus(metadata={"stage": "10.7"})
    metrics = create_metrics_registry(metadata={"stage": "10.7"})
    engine = create_policy_engine(event_bus=bus, metrics=metrics, metadata={"stage": "10.7"})

    check("Policy Stage", PLATFORM_POLICY_STAGE == "10.7")
    check("Policy Engine Type", isinstance(engine, PlatformPolicyEngine))
    check("Policy Registry Type", isinstance(engine.registry, PlatformPolicyRegistry))
    check("Event Bus Type", isinstance(bus, PlatformEventBus))
    check("Metrics Type", isinstance(metrics, PlatformMetricsRegistry))

    deny_delete = engine.deny(
        "deny-delete",
        lambda ctx: ctx.action == "delete",
        priority=10,
        description="protect platform services from delete operations",
    )
    allow_read = engine.allow("allow-read", lambda ctx: ctx.action == "read", priority=20)
    check("Policies Registered", deny_delete.active and allow_read.active and engine.registry.summary()["active_policy_count"] == 2)

    denied = engine.evaluate(PlatformPolicyContext("translator", "delete", subject="sdk"))
    check("Deny Policy", isinstance(denied, PlatformPolicyEvaluation) and denied.decision == PlatformPolicyDecision.DENY and not denied.allowed)
    check("Deny Policy Matched", denied.policy_name == "deny-delete")

    allowed = engine.evaluate({"service_name": "translator", "action": "read", "subject": "sdk"})
    check("Allow Policy", allowed.allowed and allowed.policy_name == "allow-read")

    default_allowed = engine.evaluate(PlatformPolicyContext("translator", "start"))
    check("Default Policy", default_allowed.allowed and default_allowed.reason == "default policy")

    check("Can Helper", engine.can("translator", "read") is True)
    try:
        engine.require("translator", "delete")
        require_failed = False
    except PermissionError:
        require_failed = True
    check("Require Denies", require_failed)

    check("Event Bus Integration", len(bus.history(event_type="platform.policy.evaluated")) >= 4)
    check("Metrics Integration", metrics.get("platform.policy.evaluations") is not None)

    removed = engine.registry.unregister(deny_delete.policy_id)
    check("Policy Unregistered", removed and not deny_delete.active)
    check("Inactive Policy Ignored", engine.can("translator", "delete") is True)

    summary = engine.summary()
    check("Policy Summary", summary["evaluation_count"] >= 5 and summary["allowed_count"] >= 3)

    manifest = engine.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)
    check("Future RBAC ABAC Ready", manifest["future_rbac_abac_ready"] is True)
    print("PASS")


if __name__ == "__main__":
    main()
