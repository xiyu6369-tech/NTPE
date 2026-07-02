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
from cli.commands.config_store import CLIConfigStore
from cli.commands.manifest import build_config_manifest


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="ntpe_cli_config_"))
    try:
        (tmp / "core").mkdir()
        (tmp / "runtime").mkdir()
        (tmp / "translation").mkdir()
        context = CLIContext(root=tmp)

        parser = build_parser()
        parsed = parser.parse_args(["config", "list"])
        check("Config Parser", parsed.command == "config" and parsed.config_action == "list")

        registry = build_registry()
        check("Config Registered", "config" in registry.names())

        store = CLIConfigStore(tmp)
        created = store.create(replace=True)
        check("Config Store Create", created["settings"]["provider"] == "mock")

        result_list = run_cli(["--root", str(tmp), "config", "list"], context=context)
        check("Config List", result_list.ok and result_list.data["settings"]["provider"] == "mock")

        result_get = run_cli(["--root", str(tmp), "config", "get", "provider"], context=context)
        check("Config Get", result_get.ok and result_get.data["value"] == "mock")

        result_set = run_cli(["--root", str(tmp), "config", "set", "provider", "nvidia"], context=context)
        check("Config Set", result_set.ok and result_set.data["value"] == "nvidia")

        result_validate = run_cli(["--root", str(tmp), "config", "validate"], context=context)
        check("Config Validate", result_validate.ok and result_validate.data["valid"] is True)

        export_path = tmp / "config_export.json"
        result_export = run_cli(["--root", str(tmp), "config", "export", "--output", str(export_path)], context=context)
        check("Config Export", result_export.ok and export_path.exists())

        exported = json.loads(export_path.read_text(encoding="utf-8"))
        exported["settings"]["quality"] = "high"
        export_path.write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")
        result_import = run_cli(["--root", str(tmp), "config", "import", str(export_path), "--replace"], context=context)
        check("Config Import", result_import.ok and result_import.data["config"]["settings"]["quality"] == "high")

        result_reset = run_cli(["--root", str(tmp), "config", "reset"], context=context)
        check("Config Reset", result_reset.ok and result_reset.data["settings"]["quality"] == "standard")

        provider_cfg = run_cli(["--root", str(tmp), "config", "set", "provider", "nvidia"], context=context)
        check("Provider Config", provider_cfg.ok and provider_cfg.data["config"]["settings"]["provider"] == "nvidia")

        quality_cfg = run_cli(["--root", str(tmp), "config", "set", "quality", "high"], context=context)
        check("Quality Config", quality_cfg.ok and quality_cfg.data["config"]["settings"]["quality"] == "high")

        runtime_cfg = run_cli(["--root", str(tmp), "config", "set", "runtime.checkpoint_interval", "5"], context=context)
        check("Runtime Config", runtime_cfg.ok and runtime_cfg.data["config"]["settings"]["runtime"]["checkpoint_interval"] == 5)

        session_cfg = run_cli(["--root", str(tmp), "config", "set", "session.session_dir", "sessions"], context=context)
        check("Session Config", session_cfg.ok and session_cfg.data["config"]["settings"]["session"]["session_dir"] == "sessions")

        benchmark_cfg = run_cli(["--root", str(tmp), "config", "set", "benchmark.enabled", "true"], context=context)
        check("Benchmark Config", benchmark_cfg.ok and benchmark_cfg.data["config"]["settings"]["benchmark"]["enabled"] is True)

        json_result = run_cli(["--root", str(tmp), "config", "list"], context=context)
        check("JSON Compatible Result", json_result.to_dict()["ok"] is True)

        manifest = build_config_manifest()
        check("Config Manifest", manifest["version"] == "1.0-beta-stage-06.6" and "set" in manifest["subcommands"])

        result_cli = run_cli(["--root", str(tmp)], context=context)
        check("CLI Manifest", result_cli.ok and "config" in result_cli.data["commands"])

        acceptance = run_cli(["--root", str(tmp), "config", "validate"], context=context)
        check("Acceptance Config", acceptance.ok)

        check("Backward Compatible", run_cli(["--root", str(tmp), "version"], context=context).ok)

        print("PASS")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
