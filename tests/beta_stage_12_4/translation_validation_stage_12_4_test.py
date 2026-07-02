"""Translation validation smoke test for Stage-12.4."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_4():
    api = create_rest_api()
    session = api.handle("POST", "/v1/sessions", body={"name": "translation-validation", "metadata": {"workflow": "translation"}})
    assert session.status_code == 201
    session_id = session.body["data"]["session_id"]
    pipeline = api.handle(
        "POST",
        "/v1/pipelines",
        body={
            "name": "translation-pipeline",
            "provider": "validation-provider",
            "workflow_ref": "workflow.translation",
            "stages": [{"name": "context"}, {"name": "translate"}, {"name": "quality"}],
        },
    )
    assert pipeline.status_code == 201
    pipeline_id = pipeline.body["data"]["pipeline_id"]
    validated = api.handle("POST", f"/v1/pipelines/{pipeline_id}/validate")
    assert validated.status_code == 200
    job = api.handle(
        "POST",
        "/v1/jobs",
        body={"session_id": session_id, "name": "translation-job", "pipeline": pipeline_id, "provider": "validation-provider"},
    )
    assert job.status_code == 201
    assert job.body["data"]["pipeline"] == pipeline_id


if __name__ == "__main__":
    test_translation_validation_stage_12_4()
    print("PASS")
