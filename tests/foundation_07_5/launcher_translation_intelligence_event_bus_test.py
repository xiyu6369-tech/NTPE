import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.intelligence import (
    IntelligenceEvent,
    IntelligenceEventBus,
    IntelligenceEventDispatcher,
    IntelligencePublisher,
    IntelligenceRuntimeEventFacade,
    IntelligenceSubscriber,
    TranslationIntelligenceLifecycle,
    TranslationIntelligenceRuntimeIntegration,
)
from core.intelligence.events import (
    CONSISTENCY_CHECKED,
    RUNTIME_PERSISTED,
    SEGMENT_COMPLETED,
    SEGMENT_STARTED,
    SNAPSHOT_CREATED,
)


def check(label, condition):
    print(f"{label:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    bus = IntelligenceEventBus()
    received = []
    bus.subscribe(SEGMENT_STARTED, lambda event: received.append(event))
    check("Event Registered", bus.subscriber_count(SEGMENT_STARTED) == 1)

    event = bus.publish(SEGMENT_STARTED, payload={"source_text": "정태의"}, segment_id="seg-1")
    check("Event Published", isinstance(event, IntelligenceEvent) and event.event_type == SEGMENT_STARTED)
    check("Subscriber Called", len(received) == 1 and received[0].segment_id == "seg-1")
    check("Event History", len(bus.history(SEGMENT_STARTED)) == 1)

    wildcard = IntelligenceSubscriber()
    wildcard.subscribe_to(bus, "*")
    publisher = IntelligencePublisher(bus, source="runtime")
    publisher.publish(SEGMENT_COMPLETED, {"ok": True}, segment_id="seg-1")
    check("Publisher Routed", wildcard.received[-1].event_type == SEGMENT_COMPLETED)

    dispatcher = IntelligenceEventDispatcher(bus)
    dispatched = dispatcher.route_lifecycle_event(SNAPSHOT_CREATED, scope_key="job:default")
    check("Dispatcher Routed", dispatched.source == "lifecycle" and dispatched.scope_key == "job:default")

    facade = IntelligenceRuntimeEventFacade(bus)
    started = facade.segment_started("seg-2", {"stage": "before"})
    completed = facade.segment_completed("seg-2", {"stage": "after"})
    checked = facade.consistency_checked("seg-2", {"passed": True})
    persisted = facade.runtime_persisted("job:default", {"store": "json"})
    check("Runtime Event", started.event_type == SEGMENT_STARTED and completed.event_type == SEGMENT_COMPLETED)
    check("Lifecycle Event", facade.snapshot_created("job:default").event_type == SNAPSHOT_CREATED)
    check("Consistency Event", checked.event_type == CONSISTENCY_CHECKED and checked.payload["passed"] is True)
    check("Persistence Event", persisted.event_type == RUNTIME_PERSISTED and persisted.source == "persistence")

    lifecycle = TranslationIntelligenceLifecycle()
    before = lifecycle.before_segment("seg-3", "정태의가 말했다.")
    after = lifecycle.after_segment("seg-3", "정태의가 말했다.", "鄭泰義說道。")
    bus.publish(SNAPSHOT_CREATED, payload={"snapshot": before["snapshot"]}, scope_key=before["scope"]["scope_key"])
    bus.publish(CONSISTENCY_CHECKED, payload=after.get("consistency", {}), segment_id="seg-3")
    check("Lifecycle Compatible", before["stage"] == "before_segment" and "snapshot" in after)

    runtime = TranslationIntelligenceRuntimeIntegration()
    packet = runtime.before_segment({"id": "seg-4", "text": "凱爾"})
    processed = runtime.after_segment({"id": "seg-4", "text": "凱爾"}, "凱爾")
    bus.publish(SEGMENT_STARTED, payload=packet.to_dict(), segment_id=packet.segment_id)
    bus.publish(CONSISTENCY_CHECKED, payload=processed.get("consistency", {}), segment_id="seg-4")
    check("Runtime Compatible", packet.segment_id == "seg-4" and "snapshot" in processed)

    event_dict = event.to_dict()
    restored = IntelligenceEvent.from_dict(event_dict)
    check("Event Serializable", restored.to_dict()["event_id"] == event_dict["event_id"])
    check("Backward Compatible", callable(getattr(bus, "publish")) and callable(getattr(bus, "subscribe")))
    print("PASS")


if __name__ == "__main__":
    main()
