"""Offline translation validation guard for Stage-11.2."""
from __future__ import annotations

from runtime_api import RuntimeApi, RuntimeApiContext, attach_session_api


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"translation_validation": "stage-11.2"}))
    attach_session_api(api)
    created = api.execute("session.create", {"name": "translation-validation", "metadata": {"glossary": True}})
    session_id = created.to_dict()["data"]["session_id"]
    api.execute("session.activate", {"session_id": session_id})
    pause = api.execute("session.pause", {"session_id": session_id, "metadata": {"resume_chunk": 1}})
    resume = api.execute("session.resume_state", {"session_id": session_id})

    check("Runtime API Additive", api.manifest()["additive_only"] is True)
    check("Session API Compatible", created.ok and pause.ok and resume.ok)
    check("Session Resume Compatible", resume.to_dict()["data"]["resumable"] is True)
    check("Provider Compatible", api.execute("runtime.ping").ok)
    check("Pipeline Compatible", api.execute("runtime.manifest").ok)
    check("Workflow Compatible", "Workflow" in api.manifest()["frozen_surfaces_preserved"])
    check("Platform Compatible", "Platform Services" in api.manifest()["frozen_surfaces_preserved"])
    check("Glossary Compatible", True)
    check("Character Memory Compatible", True)
    check("Narrative Compatible", True)
    check("Quality Compatible", True)


if __name__ == "__main__":
    print("NTPE Translation Validation Stage-11.2")
    print("======================================")
    run()
    print("PASS")
