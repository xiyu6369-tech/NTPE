from pathlib import Path

from core.translation_runtime import TranslationRuntime


def test_plugin_runtime_smoke(tmp_path: Path):
    runtime = TranslationRuntime(root=tmp_path)
    result = runtime.execute_pipeline_with_plugins({"smoke": True})
    assert result["status"] == "success"
    assert result["payload"]["smoke"] is True
    assert runtime.describe_plugin_runtime()["event_count"] == 10
