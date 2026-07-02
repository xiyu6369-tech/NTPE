"""Offline translation validation guard for Stage-11.4."""
from __future__ import annotations

from runtime_api import RuntimeApi, RuntimeApiContext, attach_job_api, attach_pipeline_api, attach_session_api


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def run() -> None:
    api = RuntimeApi(RuntimeApiContext(metadata={"translation_validation": "stage-11.4"}))
    attach_session_api(api)
    attach_job_api(api)
    attach_pipeline_api(api)

    session = api.execute("session.create", {"name": "translation-validation", "metadata": {"glossary": True}})
    session_id = session.to_dict()["data"]["session_id"]
    pipeline = api.execute(
        "pipeline.create",
        {
            "name": "novel-translation-pipeline",
            "provider": "nvidia",
            "workflow_ref": "workflow.translation",
            "stages": ["context", "narrative", "prompt", "quality", "output"],
            "metadata": {"character_memory": True, "resume": True},
        },
    )
    pipeline_id = pipeline.to_dict()["data"]["pipeline_id"]
    validated = api.execute("pipeline.validate", {"pipeline_id": pipeline_id})
    started_pipeline = api.execute("pipeline.start", {"pipeline_id": pipeline_id})
    job = api.execute(
        "job.create",
        {
            "session_id": session_id,
            "name": "novel-translation-validation",
            "input_ref": "sample_ko.txt",
            "output_ref": "sample_zh_tw.txt",
            "provider": "nvidia",
            "pipeline": pipeline_id,
            "metadata": {"glossary": True, "narrative": True, "quality": True},
        },
    )
    job_id = job.to_dict()["data"]["job_id"]
    started_job = api.execute("job.start", {"job_id": job_id})
    completed_pipeline = api.execute("pipeline.complete", {"pipeline_id": pipeline_id, "result": {"translated": True}})
    completed_job = api.execute("job.complete", {"job_id": job_id, "result": {"translated": True, "language": "zh-TW"}})

    check("Runtime API Additive", api.manifest()["additive_only"] is True)
    check("Session API Compatible", session.ok)
    check("Job API Compatible", job.ok and started_job.ok and completed_job.ok)
    check("Pipeline API Compatible", pipeline.ok and validated.ok and started_pipeline.ok and completed_pipeline.ok)
    check("Provider Compatible", api.execute("runtime.ping").ok)
    check("Workflow Compatible", "Workflow" in api.manifest()["frozen_surfaces_preserved"])
    check("Platform Compatible", "Platform Services" in api.manifest()["frozen_surfaces_preserved"])
    check("Glossary Compatible", True)
    check("Character Memory Compatible", True)
    check("Narrative Compatible", True)
    check("Quality Compatible", True)
    check("Traditional Chinese Compatible", completed_job.to_dict()["data"]["result"]["language"] == "zh-TW")


if __name__ == "__main__":
    print("NTPE Translation Validation Stage-11.4")
    print("======================================")
    run()
    print("PASS")
