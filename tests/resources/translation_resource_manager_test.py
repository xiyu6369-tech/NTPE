from __future__ import annotations

from pathlib import Path

from core.translation_resources import TranslationResource, TranslationResourceManager
from core.translation_runtime import TranslationRuntime


def test_resource_manager_defaults_validate(tmp_path: Path):
    manager = TranslationResourceManager(tmp_path)
    result = manager.validate()
    assert result["status"] == "success"
    assert result["resource_count"] >= 7
    assert manager.require("prompt").kind == "prompt"
    assert manager.require("provider").metadata["adapter"] == "runtime_provider"


def test_resource_manager_register_custom_resource(tmp_path: Path):
    manager = TranslationResourceManager(tmp_path)
    resource = TranslationResource(name="novel", kind="glossary", path="glossary_novel.txt")
    manager.register(resource)
    assert manager.require("glossary", "novel").path == "glossary_novel.txt"
    assert any(item["name"] == "novel" for item in manager.list("glossary"))


def test_resource_manifest_save(tmp_path: Path):
    manager = TranslationResourceManager(tmp_path)
    result = manager.save_manifest("resource-test")
    assert result["status"] == "success"
    path = Path(result["manifest_path"])
    assert path.exists()
    assert "resource-test" in path.read_text(encoding="utf-8")


def test_runtime_exposes_resource_manager(tmp_path: Path):
    runtime = TranslationRuntime(root=tmp_path)
    assert runtime.describe_resources()["status"] == "success"
    assert runtime.validate_resources()["status"] == "success"
    provider = runtime.get_resource("provider")
    assert provider["kind"] == "provider"
