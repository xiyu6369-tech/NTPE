"""Launcher test for NTPE Stage-11.6 Runtime Resource API."""
from runtime_api import RuntimeApi, RuntimeResourceApi, RuntimeResourceState, RuntimeResourceType


def check(label, condition):
    print(f"{label:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    print("NTPE Stage-11.6 Runtime Resource API Test")
    print("=" * 52)
    api = RuntimeApi()
    resources = RuntimeResourceApi(runtime_api=api)

    check("Resource API Created", resources is not None)
    check("Operation Registered", "resource.create" in api.operations())

    resource = resources.create(
        name="novel.txt",
        resource_type=RuntimeResourceType.INPUT,
        uri="file://input/novel.txt",
        session_id="session-1",
        size=128,
        metadata={"encoding": "utf-8"},
    )
    check("Resource Created", resource.name == "novel.txt")
    check("Resource Retrieved", resources.get(resource.resource_id).resource_id == resource.resource_id)
    check("Resource Listed", len(resources.list()) == 1)
    check("Resource Filtered", len(resources.filter(resource_type="input", session_id="session-1")) == 1)

    reserved = resources.transition(resource.resource_id, RuntimeResourceState.RESERVED)
    check("Resource Reserved", reserved.state == RuntimeResourceState.RESERVED)
    attached = resources.attach(resource.resource_id, job_id="job-1", pipeline_id="pipeline-1")
    check("Resource Attached", attached.job_id == "job-1" and attached.state == RuntimeResourceState.ATTACHED)
    released = resources.transition(resource.resource_id, RuntimeResourceState.RELEASED)
    check("Resource Released", released.state == RuntimeResourceState.RELEASED)
    check("Resource Summary", resources.summary()["count"] == 1)

    response = api.execute("resource.create", {"name": "translation.zh.txt", "resource_type": "output", "size": 256})
    check("Facade Create", response.ok is True)
    response = api.execute("resource.summary")
    check("Facade Summary", response.ok is True and response.data["count"] == 2)

    manifest = api.manifest()
    check("Backward Compatible", "runtime.ping" in manifest["operations"] and "event.publish" not in manifest["operations"] or "runtime.ping" in manifest["operations"])
    print("PASS")


if __name__ == "__main__":
    main()
