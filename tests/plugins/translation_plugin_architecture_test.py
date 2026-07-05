from pathlib import Path

from core.translation_plugins import TranslationPlugin, TranslationPluginManager
from core.translation_plugins.plugin import PluginResult
from core.translation_runtime import TranslationRuntime


def test_plugin_manager_defaults_are_valid(tmp_path: Path):
    manager = TranslationPluginManager(tmp_path)
    report = manager.validate()
    assert report["status"] == "success"
    assert report["plugin_count"] >= 8
    assert not report["missing"]


def test_plugin_chain_preserves_payload_and_trace(tmp_path: Path):
    manager = TranslationPluginManager(tmp_path)
    result = manager.execute_chain(kinds=("prompt", "qa"), payload={"text": "hello"})
    assert result["status"] == "success"
    assert result["payload"]["text"] == "hello"
    assert result["payload"]["plugin_trace"] == ["default", "default"]


def test_custom_plugin_can_replace_default(tmp_path: Path):
    manager = TranslationPluginManager(tmp_path)

    def handler(context):
        payload = dict(context.payload)
        payload["formatted"] = True
        return PluginResult(status="success", payload=payload, metadata={"custom": True})

    manager.register(TranslationPlugin(name="default", kind="formatter", handler=handler), replace=True)
    result = manager.execute("formatter", payload={"value": "繁體"})
    assert result["status"] == "success"
    assert result["payload"]["formatted"] is True
    assert result["metadata"]["custom"] is True


def test_runtime_exposes_plugin_contract(tmp_path: Path):
    runtime = TranslationRuntime(root=tmp_path)
    assert runtime.validate_plugins()["status"] == "success"
    assert runtime.describe_plugins()["plugin_count"] >= 8
    assert runtime.get_plugin("provider") is not None
    result = runtime.execute_plugin_chain(kinds=("provider", "qa"), payload={"source": "안녕"})
    assert result["status"] == "success"
    assert result["payload"]["source"] == "안녕"
