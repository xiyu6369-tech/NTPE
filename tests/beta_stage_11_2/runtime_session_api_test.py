"""NTPE 1.0 Beta Stage-11.2 Runtime Session API Test."""
from __future__ import annotations

from runtime_api import RuntimeApi, RuntimeApiContext, RuntimeSessionApi, RuntimeSessionState, attach_session_api


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"suite": "stage-11.2"}))
    session_api = attach_session_api(api)

    check("Session API Created", isinstance(session_api, RuntimeSessionApi))
    check("Core Preserved", api.execute("runtime.ping").ok)
    check("Operations Registered", "session.create" in api.operations())

    created = api.execute("session.create", {"name": "validation", "metadata": {"file": "sample.txt"}})
    check("Session Created", created.ok)
    session_id = created.to_dict()["data"]["session_id"]
    check("Session State Created", created.to_dict()["data"]["state"] == RuntimeSessionState.CREATED.value)

    activated = api.execute("session.activate", {"session_id": session_id})
    check("Session Activated", activated.ok and activated.to_dict()["data"]["state"] == "active")

    paused = api.execute("session.pause", {"session_id": session_id, "metadata": {"chunk": 7}})
    check("Session Paused", paused.ok and paused.to_dict()["data"]["metadata"]["chunk"] == 7)

    resume = api.execute("session.resume_state", {"session_id": session_id})
    check("Resume State", resume.ok and resume.to_dict()["data"]["resumable"] is True)

    listed = api.execute("session.list")
    check("Session Listed", listed.ok and listed.to_dict()["data"]["count"] == 1)

    completed = api.execute("session.complete", {"session_id": session_id})
    check("Session Completed", completed.ok and completed.to_dict()["data"]["state"] == "completed")

    missing = api.execute("session.get", {"session_id": "missing"})
    check("Missing Session Error", not missing.ok and missing.error.status == 500)

    check("Backward Compatibility", api.manifest()["additive_only"] is True)


if __name__ == "__main__":
    print("NTPE 1.0 Beta Stage-11.2 Runtime Session API Test")
    print("======================================================")
    run()
    print("PASS")
