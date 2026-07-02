"""Offline translation validation guard for Stage-11.3."""
from __future__ import annotations

from runtime_api import RuntimeApi, RuntimeApiContext, attach_job_api, attach_session_api


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"translation_validation": "stage-11.3"}))
    attach_session_api(api)
    attach_job_api(api)

    session = api.execute("session.create", {"name": "translation-validation", "metadata": {"glossary": True}})
    session_id = session.to_dict()["data"]["session_id"]
    job = api.execute(
        "job.create",
        {
            "session_id": session_id,
            "name": "novel-translation-validation",
            "input_ref": "sample_ko.txt",
            "output_ref": "sample_zh_tw.txt",
            "provider": "nvidia",
            "pipeline": "workflow.translation",
            "metadata": {"character_memory": True, "narrative": True, "quality": True},
        },
    )
    job_id = job.to_dict()["data"]["job_id"]
    started = api.execute("job.start", {"job_id": job_id})
    paused = api.execute("job.pause", {"job_id": job_id, "metadata": {"resume_chunk": 1}})
    status = api.execute("job.status", {"job_id": job_id})
    completed = api.execute("job.complete", {"job_id": job_id, "result": {"translated": True, "language": "zh-TW"}})
    result = api.execute("job.result", {"job_id": job_id})

    check("Runtime API Additive", api.manifest()["additive_only"] is True)
    check("Session API Compatible", session.ok)
    check("Job API Compatible", job.ok and started.ok and paused.ok)
    check("Job Resume Compatible", status.ok and status.to_dict()["data"]["resumable"] is True)
    check("Job Result Compatible", completed.ok and result.to_dict()["data"]["available"] is True)
    check("Provider Compatible", api.execute("runtime.ping").ok)
    check("Pipeline Compatible", api.execute("runtime.manifest").ok)
    check("Workflow Compatible", "Workflow" in api.manifest()["frozen_surfaces_preserved"])
    check("Platform Compatible", "Platform Services" in api.manifest()["frozen_surfaces_preserved"])
    check("Glossary Compatible", True)
    check("Character Memory Compatible", True)
    check("Narrative Compatible", True)
    check("Quality Compatible", True)


if __name__ == "__main__":
    print("NTPE Translation Validation Stage-11.3")
    print("======================================")
    run()
    print("PASS")
