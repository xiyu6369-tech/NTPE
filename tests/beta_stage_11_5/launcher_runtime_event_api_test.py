"""Launcher test for NTPE Stage-11.5 Runtime Event API."""
from runtime_api import RuntimeApi, RuntimeEventApi, RuntimeEventSeverity, RuntimeEventType


def check(label, condition):
    print(f"{label:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    print("NTPE Stage-11.5 Runtime Event API Test")
    print("=" * 48)
    api = RuntimeApi()
    events = RuntimeEventApi(runtime_api=api)

    check("Event API Created", events is not None)
    check("Operation Registered", "event.publish" in api.operations())

    event = events.publish(
        name="job.started",
        event_type=RuntimeEventType.JOB,
        severity=RuntimeEventSeverity.INFO,
        job_id="job-1",
        message="Job started",
        payload={"step": 1},
    )
    check("Event Published", event.name == "job.started")
    check("Event Retrieved", events.get(event.event_id).event_id == event.event_id)
    check("Event Listed", len(events.list()) == 1)
    check("Event Filtered", len(events.filter(event_type="job", job_id="job-1")) == 1)
    check("Event Summary", events.summary()["count"] == 1)

    response = api.execute("event.publish", {"name": "pipeline.completed", "event_type": "pipeline", "severity": "info"})
    check("Facade Publish", response.ok is True)
    response = api.execute("event.summary")
    check("Facade Summary", response.ok is True and response.data["count"] == 2)

    manifest = api.manifest()
    check("Backward Compatible", "runtime.ping" in manifest["operations"])
    print("PASS")


if __name__ == "__main__":
    main()
