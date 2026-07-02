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
from cli.commands.plugin_store import CLIPluginStore
from cli.commands.manifest import build_plugin_manifest


def check(name: str, condition: bool) -> bool:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    return bool(condition)


def main() -> int:
    ok = True
    temp = Path(tempfile.mkdtemp(prefix="ntpe_plugin_cli_"))
    try:
        ctx = CLIContext(root=temp)
        parser = build_parser()
        args = parser.parse_args(["plugin", "list"])
        ok &= check("Plugin Parser", args.command == "plugin" and args.plugin_action == "list")

        registry = build_registry()
        ok &= check("Plugin Registered", "plugin" in registry.names())

        store = CLIPluginStore(temp)
        initial = store.ensure()
        ok &= check("Plugin Store Create", "plugins" in initial and len(initial["plugins"]) >= 4)

        result = run_cli(["plugin", "list"], context=ctx)
        ok &= check("Plugin List", result.ok and result.data["plugins"])

        result = run_cli(["plugin", "info", "context"], context=ctx)
        ok &= check("Plugin Info", result.ok and result.data["plugin"]["name"] == "context")

        result = run_cli(["plugin", "disable", "context"], context=ctx)
        ok &= check("Plugin Disable", result.ok and result.data["plugin"]["enabled"] is False)

        result = run_cli(["plugin", "list", "--disabled"], context=ctx)
        ok &= check("Plugin Disabled Filter", result.ok and any(p["name"] == "context" for p in result.data["plugins"]))

        result = run_cli(["plugin", "enable", "context"], context=ctx)
        ok &= check("Plugin Enable", result.ok and result.data["plugin"]["enabled"] is True)

        package = temp / "sample_plugin.json"
        package.write_text(json.dumps({"name": "sample", "version": "0.1.0", "kind": "adapter", "enabled": True}), encoding="utf-8")
        result = run_cli(["plugin", "install", str(package)], context=ctx)
        ok &= check("Plugin Install", result.ok and result.data["plugin"]["name"] == "sample")

        result = run_cli(["plugin", "validate"], context=ctx)
        ok &= check("Plugin Validate", result.ok and result.data["validation"]["valid"])

        result = run_cli(["plugin", "uninstall", "sample"], context=ctx)
        ok &= check("Plugin Uninstall", result.ok and result.data["plugin"]["name"] == "sample")

        result = run_cli(["--json", "plugin", "list"], context=ctx)
        ok &= check("JSON Compatible Result", result.ok and "plugins" in result.data)

        manifest = build_plugin_manifest()
        ok &= check("Plugin Manifest", manifest["component"] == "cli.plugin" and "plugin" in manifest["commands"])

        ok &= check("CLI Manifest", any("plugin" == name for name in build_registry().names()))

        result = run_cli(["plugin", "list"], context=ctx)
        ok &= check("Acceptance Plugin", result.ok and result.exit_code == 0)

        result = run_cli(["version"], context=ctx)
        ok &= check("Backward Compatible", result.ok)

        print("PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
