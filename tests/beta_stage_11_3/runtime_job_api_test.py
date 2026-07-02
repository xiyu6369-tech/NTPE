"""NTPE 1.0 Beta Stage-11.3 Runtime Job API Test."""
from __future__ import annotations

from runtime_api import (
    RuntimeApi,
    RuntimeApiContext,
    RuntimeJobApi,
    RuntimeJobState,
    attach_job_api,
    attach_session_api,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"suite": "stage-11.3"}))
    session_api = attach_session_api(api)
    job_api = attach_job_api(api)

    check("Job API Created", isinstance(job_api, RuntimeJobApi))
    check("Core Preserved", api.execute("runtime.ping").ok)
    check("Session Preserved", "session.create" in api.operations())
    check("Job Operations Registered", "job.create" in api.operations())

    session = session_api.create(name="job-validation")
    created = api.execute(
        "job.create",
        {
            "session_id": session.session_id,
            "name": "translate-sample",
            "input_ref": "sample_ko.txt",
            "output_ref": "sample_zh.txt",
            "provider": "nvidia",
            "pipeline": "translation",
            "metadata": {"glossary": True},
        },
    )
    check("Job Created", created.ok)
    job_id = created.to_dict()["data"]["job_id"]
    check("Job State Created", created.to_dict()["data"]["state"] == RuntimeJobState.CREATED.value)

    started = api.execute("job.start", {"job_id": job_id, "metadata": {"chunk": 1}})
    check("Job Started", started.ok and started.to_dict()["data"]["state"] == "started")

    paused = api.execute("job.pause", {"job_id": job_id, "metadata": {"resume_chunk": 1}})
    check("Job Paused", paused.ok and paused.to_dict()["data"]["metadata"]["resume_chunk"] == 1)

    status = api.execute("job.status", {"job_id": job_id})
    check("Job Status", status.ok and status.to_dict()["data"]["resumable"] is True)

    resumed = api.execute("job.resume", {"job_id": job_id})
    check("Job Resumed", resumed.ok and resumed.to_dict()["data"]["state"] == "resumed")

    stopped = api.execute("job.stop", {"job_id": job_id})
    check("Job Stopped", stopped.ok and stopped.to_dict()["data"]["state"] == "stopped")

    completed = api.execute("job.complete", {"job_id": job_id, "result": {"segments": 1, "ok": True}})
    check("Job Completed", completed.ok and completed.to_dict()["data"]["state"] == "completed")

    result = api.execute("job.result", {"job_id": job_id})
    check("Job Result", result.ok and result.to_dict()["data"]["available"] is True)

    listed = api.execute("job.list")
    check("Job Listed", listed.ok and listed.to_dict()["data"]["count"] == 1)

    cancel_job = api.execute("job.create", {"name": "cancel-sample"})
    cancel_id = cancel_job.to_dict()["data"]["job_id"]
    cancelled = api.execute("job.cancel", {"job_id": cancel_id})
    check("Job Cancelled", cancelled.ok and cancelled.to_dict()["data"]["state"] == "cancelled")

    missing = api.execute("job.get", {"job_id": "missing"})
    check("Missing Job Error", not missing.ok and missing.error.status == 500)

    check("Backward Compatibility", api.manifest()["additive_only"] is True)


if __name__ == "__main__":
    print("NTPE 1.0 Beta Stage-11.3 Runtime Job API Test")
    print("=================================================")
    run()
    print("PASS")
