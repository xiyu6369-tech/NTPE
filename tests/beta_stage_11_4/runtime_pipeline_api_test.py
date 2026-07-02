"""NTPE 1.0 Beta Stage-11.4 Runtime Pipeline API Test."""
from __future__ import annotations

from runtime_api import (
    RuntimeApi,
    RuntimeApiContext,
    RuntimePipelineApi,
    RuntimePipelineState,
    attach_job_api,
    attach_pipeline_api,
    attach_session_api,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"suite": "stage-11.4"}))
    attach_session_api(api)
    attach_job_api(api)
    pipeline_api = attach_pipeline_api(api)

    check("Pipeline API Created", isinstance(pipeline_api, RuntimePipelineApi))
    check("Core Preserved", api.execute("runtime.ping").ok)
    check("Session Preserved", "session.create" in api.operations())
    check("Job Preserved", "job.create" in api.operations())
    check("Pipeline Registered", "pipeline.create" in api.operations())

    created = api.execute(
        "pipeline.create",
        {
            "name": "translation-pipeline",
            "provider": "nvidia",
            "workflow_ref": "workflow.translation",
            "stages": [
                {"name": "context", "component": "context_plugin", "order": 1},
                {"name": "narrative", "component": "narrative_plugin", "order": 2},
                {"name": "quality", "component": "quality_plugin", "order": 3},
            ],
            "metadata": {"glossary": True},
        },
    )
    check("Pipeline Created", created.ok)
    pipeline_id = created.to_dict()["data"]["pipeline_id"]
    check("Pipeline State Created", created.to_dict()["data"]["state"] == RuntimePipelineState.CREATED.value)
    check("Pipeline Stages", created.to_dict()["data"]["stage_count"] == 3)

    added = api.execute("pipeline.add_stage", {"pipeline_id": pipeline_id, "stage": {"name": "output", "order": 4}})
    check("Pipeline Stage Added", added.ok and added.to_dict()["data"]["stage_count"] == 4)

    validated = api.execute("pipeline.validate", {"pipeline_id": pipeline_id})
    check("Pipeline Validated", validated.ok and validated.to_dict()["data"]["state"] == "validated")

    started = api.execute("pipeline.start", {"pipeline_id": pipeline_id, "metadata": {"chunk": 1}})
    check("Pipeline Started", started.ok and started.to_dict()["data"]["state"] == "started")

    paused = api.execute("pipeline.pause", {"pipeline_id": pipeline_id, "metadata": {"resume_chunk": 1}})
    check("Pipeline Paused", paused.ok and paused.to_dict()["data"]["metadata"]["resume_chunk"] == 1)

    status = api.execute("pipeline.status", {"pipeline_id": pipeline_id})
    check("Pipeline Status", status.ok and status.to_dict()["data"]["resumable"] is True)

    resumed = api.execute("pipeline.resume", {"pipeline_id": pipeline_id})
    check("Pipeline Resumed", resumed.ok and resumed.to_dict()["data"]["state"] == "resumed")

    completed = api.execute("pipeline.complete", {"pipeline_id": pipeline_id, "result": {"segments": 1, "ok": True}})
    check("Pipeline Completed", completed.ok and completed.to_dict()["data"]["state"] == "completed")

    summary = api.execute("pipeline.summary", {"pipeline_id": pipeline_id})
    check("Pipeline Summary", summary.ok and summary.to_dict()["data"]["stage_count"] == 4)

    listed = api.execute("pipeline.list")
    check("Pipeline Listed", listed.ok and listed.to_dict()["data"]["count"] == 1)

    missing = api.execute("pipeline.get", {"pipeline_id": "missing"})
    check("Missing Pipeline Error", not missing.ok and missing.error.status == 500)

    check("Backward Compatibility", api.manifest()["additive_only"] is True)


if __name__ == "__main__":
    print("NTPE 1.0 Beta Stage-11.4 Runtime Pipeline API Test")
    print("======================================================")
    run()
    print("PASS")
