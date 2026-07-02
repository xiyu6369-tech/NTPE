from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.context import CLIContext
from cli.main import build_registry, run_cli
from cli.parser import build_parser
from cli.manifest import build_cli_manifest
from cli.commands.manifest import build_project_manifest
from cli.commands.project_manager import ProjectManager
from cli.commands.project_model import PROJECT_FILE, ProjectMetadata, ProjectValidation


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    base = Path(tempfile.mkdtemp(prefix="ntpe_cli_project_"))
    try:
        for folder in ["core", "runtime", "translation", "benchmark", "tests", "config", "cli"]:
            (base / folder).mkdir(parents=True, exist_ok=True)
        (base / "VERSION.txt").write_text("1.0.0-beta", encoding="utf-8")
        ctx = CLIContext.discover(base)

        parser = build_parser()
        parsed = parser.parse_args(["project", "create", str(base / "project_a"), "--name", "Project A"])
        check("Project Parser", parsed.command == "project" and parsed.project_action == "create")

        registry = build_registry()
        check("Project Registered", "project" in registry.names())

        manager = ProjectManager(base)
        created = manager.create(base / "project_model", name="Model Project")
        check("Project Manager Create", (base / "project_model" / PROJECT_FILE).exists() and created["project"]["name"] == "Model Project")

        opened = manager.open(base / "project_model")
        check("Project Manager Open", opened["project"]["name"] == "Model Project")

        validation = manager.validate(base / "project_model")
        check("Project Validation Model", isinstance(validation, ProjectValidation) and validation.ok)

        create_result = run_cli(["--root", str(base), "project", "create", str(base / "project_cli"), "--name", "CLI Project"])
        check("Project Create", create_result.ok and create_result.data["project"]["name"] == "CLI Project")

        open_result = run_cli(["--root", str(base), "project", "open", str(base / "project_cli")])
        check("Project Open", open_result.ok and open_result.data["project"]["name"] == "CLI Project")

        info_result = run_cli(["--root", str(base), "project", "info", str(base / "project_cli")])
        check("Project Info", info_result.ok and "directories" in info_result.data)

        validate_result = run_cli(["--root", str(base), "project", "validate", str(base / "project_cli")])
        check("Project Validate", validate_result.ok and validate_result.data["validation"]["ok"] is True)

        list_result = run_cli(["--root", str(base), "project", "list", str(base)])
        check("Project List", list_result.ok and list_result.data["count"] >= 2)

        export_path = base / "project_export.json"
        export_result = run_cli(["--root", str(base), "project", "export", str(base / "project_cli"), "--output", str(export_path)])
        check("Project Export", export_result.ok and export_path.exists())

        import_result = run_cli(["--root", str(base), "project", "import", str(export_path), "--output", str(base / "project_imported")])
        check("Project Import", import_result.ok and (base / "project_imported" / PROJECT_FILE).exists())

        replace_result = run_cli(["--root", str(base), "project", "import", str(export_path), "--output", str(base / "project_imported"), "--replace"])
        check("Project Replace Import", replace_result.ok)

        bad_validate = run_cli(["--root", str(base), "project", "validate", str(base / "missing")])
        check("Project Validate Failure", not bad_validate.ok and bad_validate.exit_code == 1)

        metadata = ProjectMetadata.from_dict({"name": "Roundtrip", "root": str(base)})
        check("Project Metadata", metadata.to_dict()["name"] == "Roundtrip")

        manifest = build_project_manifest()
        check("Project Manifest", manifest["version"] == "1.0-beta-stage-06.2" and "create" in manifest["actions"])

        cli_manifest = build_cli_manifest()
        check("CLI Manifest", cli_manifest["version"] == "0.6.2" and "project" in cli_manifest["commands"])

        check("Acceptance Project", run_cli(["--root", str(base), "project", "info", str(base / "project_cli")]).ok)
        check("Backward Compatible", run_cli(["--root", str(base), "version"]).ok and run_cli(["--root", str(base), "doctor"]).ok and run_cli(["--root", str(base), "translate", str(base / "VERSION.txt"), "--output", str(base / "out"), "--dry-run"]).ok)
        print("PASS")
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
