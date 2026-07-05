from pathlib import Path
import json

from core.translation_plugins.marketplace import (
    PluginMarketplaceManager,
    MarketplacePluginManifest,
    compare_versions,
)


def write_package(tmp_path: Path, plugin_id: str = "sample.qa") -> Path:
    package = tmp_path / plugin_id
    package.mkdir()
    payload = {
        "plugin_id": plugin_id,
        "name": "Sample QA Plugin",
        "version": "1.0.0",
        "api_version": "1.2",
        "ntpe_min_version": "1.1.0",
        "capabilities": ["qa"],
        "dependencies": [],
        "entrypoint": "sample:Plugin",
    }
    (package / "plugin_manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    return package


def test_manifest_validation_accepts_supported_plugin():
    manifest = MarketplacePluginManifest(
        plugin_id="formatter.tw",
        name="Taiwan Formatter",
        version="1.0.0",
        capabilities=("formatter",),
    )
    assert manifest.validate("1.2.0")["status"] == "success"


def test_marketplace_install_list_uninstall(tmp_path):
    package = write_package(tmp_path)
    root = tmp_path / "project"
    manager = PluginMarketplaceManager(root)

    installed = manager.install(package)
    assert installed["status"] == "success"
    assert manager.list_plugins()["plugin_count"] == 1
    assert manager.validate()["status"] == "success"

    removed = manager.uninstall("sample.qa")
    assert removed["status"] == "success"
    assert manager.list_plugins()["plugin_count"] == 0


def test_marketplace_dependency_guard(tmp_path):
    package = write_package(tmp_path, "needs.base")
    manifest_path = package / "plugin_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["dependencies"] = ["missing.base"]
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    result = PluginMarketplaceManager(tmp_path / "project").install(package)
    assert result["status"] == "failed"
    assert result["missing_dependencies"] == ["missing.base"]


def test_version_compare():
    assert compare_versions("1.2.0", "1.1.9") == 1
    assert compare_versions("1.2.0", "1.2.0") == 0
    assert compare_versions("1.2.0-alpha", "1.2.0") == -1
