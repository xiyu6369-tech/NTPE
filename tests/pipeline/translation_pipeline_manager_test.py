from __future__ import annotations

from pathlib import Path

from core.translation_pipeline import TranslationPipelineManager
from core.translation_runtime import TranslationRuntime


EXPECTED_PIPELINE = [
    "Encoding",
    "Chunk",
    "Context",
    "Glossary",
    "Character Memory",
    "Prompt Builder",
    "AI Provider",
    "QA",
    "Taiwan Formatter",
    "Output",
]


def test_pipeline_manifest_matches_official_runtime_contract(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    description = runtime.describe_pipeline()

    assert description["status"] == "success"
    manifest = description["manifest"]
    assert manifest["pipeline_version"] == "1.2-professional-stage-06"
    assert manifest["compatibility_floor"] == "1.1-lts-stable"
    assert [step["name"] for step in manifest["steps"]] == EXPECTED_PIPELINE


def test_pipeline_validation_is_stable_and_exported(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    validation = runtime.validate_pipeline()
    compatibility = runtime.validate_compatibility()

    assert validation["status"] == "success"
    assert validation["missing_steps"] == []
    assert validation["wrong_order"] is False
    assert validation["duplicate_steps"] is False
    assert "describe_pipeline" not in compatibility["missing_entrypoints"]
    assert any(item["name"] == "translation_pipeline" for item in compatibility["capabilities"])


def test_pipeline_execute_records_all_steps_in_order(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    result = runtime.execute_pipeline(payload={"source": "sample"})

    assert result["status"] == "success"
    assert result["state"]["status"] == "success"
    assert result["state"]["completed_steps"] == EXPECTED_PIPELINE
    assert result["payload"]["pipeline_trace"] == EXPECTED_PIPELINE
    assert len(result["results"]) == len(EXPECTED_PIPELINE)


def test_pipeline_custom_handler_can_fail_safely(tmp_path: Path) -> None:
    manager = TranslationPipelineManager(tmp_path, runtime=object())

    def fail_qa(context: dict) -> dict:
        raise RuntimeError("QA blocked")

    result = manager.execute(handlers={"QA": fail_qa})

    assert result["status"] == "failed"
    assert result["state"]["failed_step"] == "QA"
    assert result["state"]["last_error"] == "QA blocked"


def test_pipeline_manifest_can_be_saved(tmp_path: Path) -> None:
    runtime = TranslationRuntime(root=tmp_path)
    saved = runtime.save_pipeline_manifest("stage06-test")

    assert saved["status"] == "success"
    assert saved["pipeline_id"] == "stage06-test"
    assert Path(saved["manifest_path"]).exists()
