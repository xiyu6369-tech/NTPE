"""Focused assertions for Runtime Resource API."""
from runtime_api import RuntimeApi, RuntimeResourceApi


def test_resource_lifecycle():
    api = RuntimeApi()
    resources = RuntimeResourceApi(runtime_api=api)
    created = resources.create(name="cache.json", resource_type="cache", owner_id="runtime", size=10)
    assert created.resource_type.value == "cache"
    assert resources.summary()["total_size"] == 10
    assert api.execute("resource.reserve", {"resource_id": created.resource_id}).ok is True
    assert api.execute("resource.attach", {"resource_id": created.resource_id, "session_id": "s1"}).data["session_id"] == "s1"
    assert api.execute("resource.release", {"resource_id": created.resource_id}).data["state"] == "released"


if __name__ == "__main__":
    test_resource_lifecycle()
    print("PASS")
