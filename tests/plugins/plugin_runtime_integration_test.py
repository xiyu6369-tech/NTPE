from pathlib import Path

from core.translation_plugins import TranslationPluginRuntime
from core.translation_runtime import TranslationRuntime


def test_plugin_runtime_validates_official_pipeline_map(tmp_path: Path):
    runtime = TranslationPluginRuntime(tmp_path)
    result = runtime.validate()
    assert result["status"] == "success"
    assert result["pipeline_plugin_map"]["AI Provider"] == "provider"
    assert result["manager"]["plugin_count"] >= 8


def test_plugin_runtime_executes_pipeline_handlers(tmp_path: Path):
    runtime = TranslationRuntime(root=tmp_path)
    result = runtime.execute_pipeline_with_plugins({"source": "abc"})
    assert result["status"] == "success"
    assert result["payload"]["source"] == "abc"
    assert len(result["payload"]["plugin_runtime_trace"]) == 10
    assert result["payload"]["plugin_runtime_trace"][-1]["step"] == "Output"


def test_runtime_exposes_plugin_runtime_contract(tmp_path: Path):
    runtime = TranslationRuntime(root=tmp_path)
    validation = runtime.validate_plugin_runtime()
    description = runtime.describe_plugin_runtime()
    assert validation["status"] == "success"
    assert description["version"] == "1.2-professional-stage-09"
    assert description["event_count"] == 0
