import json
from pathlib import Path

from core.translation_plugins.marketplace.cli import PluginMarketplaceCLI, render_result


def write_package(tmp_path: Path, plugin_id: str = "cli.qa") -> Path:
    package = tmp_path / plugin_id
    package.mkdir()
    payload = {
        "plugin_id": plugin_id,
        "name": "CLI QA Plugin",
        "version": "1.0.0",
        "api_version": "1.2",
        "ntpe_min_version": "1.1.0",
        "capabilities": ["qa"],
        "dependencies": [],
        "entrypoint": "cli_qa:Plugin",
    }
    (package / "plugin_manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    return package


def parse_args(argv):
    return PluginMarketplaceCLI.build_parser().parse_args(argv)


def test_cli_inspect_package(tmp_path):
    package = write_package(tmp_path)
    cli = PluginMarketplaceCLI(tmp_path / "project")
    result = cli.execute(parse_args(["inspect", str(package)]))
    assert result["status"] == "success"
    assert result["manifest"]["plugin_id"] == "cli.qa"


def test_cli_install_list_validate_uninstall(tmp_path):
    package = write_package(tmp_path)
    cli = PluginMarketplaceCLI(tmp_path / "project")

    assert cli.execute(parse_args(["install", str(package)]))["status"] == "success"
    listing = cli.execute(parse_args(["list"]))
    assert listing["plugin_count"] == 1
    assert cli.execute(parse_args(["validate"]))["status"] == "success"
    assert cli.execute(parse_args(["doctor"]))["status"] == "success"
    assert cli.execute(parse_args(["uninstall", "cli.qa"]))["status"] == "success"
    assert cli.execute(parse_args(["list"]))["plugin_count"] == 0


def test_cli_render_json_and_text():
    result = {"status": "success", "plugin_count": 0, "plugins": []}
    assert '"status": "success"' in render_result(result, json_output=True)
    assert "plugin_count: 0" in render_result(result, json_output=False)
