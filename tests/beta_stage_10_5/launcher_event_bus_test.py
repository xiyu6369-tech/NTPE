"""NTPE 1.0 Beta Stage-10.5 Event Bus test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_EVENT_BUS_STAGE,
    PlatformEvent,
    PlatformEventBus,
    PlatformEventBridge,
    create_event_bridge,
    create_event_bus,
    create_platform_service_host,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.5 Event Bus Test")
    print("=" * 78)

    received = []
    wildcard_received = []

    bus = create_event_bus(metadata={"stage": "10.5"})
    check("Event Bus Stage", PLATFORM_EVENT_BUS_STAGE == "10.5")
    check("Event Bus Type", isinstance(bus, PlatformEventBus))

    sub = bus.subscribe("platform.service.started", lambda event: received.append(event.to_dict()))
    wildcard = bus.subscribe("platform.service.*", lambda event: wildcard_received.append(event.event_type))
    check("Subscription Created", sub.active and wildcard.active)

    event = bus.publish("platform.service.started", {"service": "translator"}, source="test", topic="service")
    check("Event Created", isinstance(event, PlatformEvent) and event.event_type == "platform.service.started")
    check("Exact Delivery", len(received) == 1 and received[0]["payload"]["service"] == "translator")
    check("Wildcard Delivery", wildcard_received == ["platform.service.started"])

    history = bus.history(event_type="platform.service.started")
    check("History", len(history) == 1 and history[0].event_id == event.event_id)

    deliveries = bus.deliveries(event_id=event.event_id)
    check("Delivery Records", len(deliveries) == 2 and all(item.ok for item in deliveries))

    removed = bus.unsubscribe(sub.subscriber_id)
    bus.publish("platform.service.started", {"service": "quality"})
    check("Unsubscribe", removed and len(received) == 1 and len(wildcard_received) == 2)

    bridge = create_event_bridge(bus, source="test.bridge", metadata={"component": "bridge"})
    bridge_event = bridge.emit("platform.bridge.ready", {"ready": True}, topic="bridge")
    check("Bridge Emit", isinstance(bridge, PlatformEventBridge) and bridge_event.source == "test.bridge")

    host = create_platform_service_host(event_bus=bus, metadata={"stage": "10.5"})
    host.register_service("evented_service", object())
    host.manager.start_service("evented_service")
    check("Service Manager Bridge", len(bus.history(event_type="platform.service.started")) >= 3)

    summary = bus.summary()
    check("Event Summary", summary["event_count"] >= 4 and summary["delivery_count"] >= 4)

    manifest = bus.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)
    print("PASS")


if __name__ == "__main__":
    main()
