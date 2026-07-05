import json
import zipfile
from pathlib import Path

from core.translation_plugins.marketplace import PluginPackageBuilder, PluginPackagePublisher
from core.translation_plugins.marketplace.cli import PluginMarketplaceCLI


def write_plugin_source(tmp_path: Path, plugin_id: str = "builder.qa") -> Path:
    source = tmp_path / plugin_id
    source.mkdir()
    payload = {
        "plugin_id": plugin_id,
        "name": "Builder QA Plugin",
        "version": "1.0.0",
        "api_version": "1.2",
        "ntpe_min_version": "1.1.0",
        "capabilities": ["qa"],
        "dependencies": [],
        "entrypoint": "builder_qa:Plugin",
    }
    (source / "plugin_manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    (source / "builder_qa.py").write_text("class Plugin:\n    pass\n", encoding="utf-8")
    (source / "README.md").write_text("# plugin\n", encoding="utf-8")
    return source


def parse_args(argv):
    return PluginMarketplaceCLI.build_parser().parse_args(argv)


def test_builder_creates_zip_and_metadata(tmp_path):
    source = write_plugin_source(tmp_path)
    result = PluginPackageBuilder.create(source, tmp_path / "dist").build()

    assert result["status"] == "success"
    package_path = Path(result["package_path"])
    metadata_path = Path(result["metadata_path"])
    assert package_path.exists()
    assert metadata_path.exists()
    assert result["file_count"] == 3

    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
    assert "plugin_manifest.json" in names
    assert "builder_qa.py" in names
    assert "README.md" in names


def test_builder_rejects_missing_entrypoint(tmp_path):
    source = write_plugin_source(tmp_path, "broken.qa")
    (source / "builder_qa.py").unlink()
    result = PluginPackageBuilder.create(source, tmp_path / "dist").build()

    assert result["status"] == "failed"
    assert any("entrypoint module not found" in item for item in result["errors"])


def test_publisher_adds_metadata_to_local_index(tmp_path):
    source = write_plugin_source(tmp_path)
    built = PluginPackageBuilder.create(source, tmp_path / "dist").build()
    publisher = PluginPackagePublisher.create(tmp_path / "repository")

    published = publisher.publish_metadata(built["metadata_path"])
    listing = publisher.list_published()

    assert published["status"] == "success"
    assert listing["package_count"] == 1
    assert listing["packages"][0]["plugin_id"] == "builder.qa"


def test_cli_build_publish_and_list_published(tmp_path):
    source = write_plugin_source(tmp_path, "cli.builder")
    root = tmp_path / "project"
    cli = PluginMarketplaceCLI(root)

    built = cli.execute(parse_args(["build", str(source), "--output", str(tmp_path / "dist")]))
    assert built["status"] == "success"

    published = cli.execute(parse_args(["publish", built["metadata_path"], "--repository", str(root / "plugins" / "published")]))
    assert published["status"] == "success"

    listing = cli.execute(parse_args(["published"]))
    assert listing["package_count"] == 1
