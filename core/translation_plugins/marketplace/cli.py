from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .manager import PluginMarketplaceManager
from .package import MarketplacePluginPackage


class PluginMarketplaceCLI:
    """Command interface for the NTPE plugin marketplace.

    The CLI layer owns argument parsing and result rendering only. Marketplace
    state changes remain delegated to PluginMarketplaceManager so the command
    surface stays backward compatible with the Stage-11 marketplace API.
    """

    def __init__(self, root: str | Path, ntpe_version: str = "1.2.0") -> None:
        self.root = Path(root)
        self.manager = PluginMarketplaceManager(self.root, ntpe_version=ntpe_version)

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="NTPE Plugin Marketplace CLI")
        parser.add_argument("--root", default=None, help="NTPE project root. Defaults to current entrypoint root.")
        parser.add_argument("--ntpe-version", default="1.2.0", help="NTPE version used for compatibility checks.")
        parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")

        sub = parser.add_subparsers(dest="command")

        sub.add_parser("list", help="List installed marketplace plugins.")
        sub.add_parser("validate", help="Validate the installed marketplace index.")

        inspect_parser = sub.add_parser("inspect", help="Inspect and validate a plugin package without installing it.")
        inspect_parser.add_argument("package")

        install_parser = sub.add_parser("install", help="Install a plugin package.")
        install_parser.add_argument("package")
        install_parser.add_argument("--replace", action="store_true", help="Replace an existing installed plugin.")

        uninstall_parser = sub.add_parser("uninstall", help="Uninstall a plugin by id.")
        uninstall_parser.add_argument("plugin_id")

        sub.add_parser("doctor", help="Run marketplace health checks.")
        return parser

    def execute(self, args: argparse.Namespace) -> dict[str, Any]:
        command = args.command or "list"
        if command == "install":
            return self.manager.install(args.package, replace=args.replace)
        if command == "uninstall":
            return self.manager.uninstall(args.plugin_id)
        if command == "validate":
            return self.manager.validate()
        if command == "inspect":
            package = MarketplacePluginPackage.load(args.package)
            result = package.validate(ntpe_version=args.ntpe_version)
            result["manifest"] = package.manifest.to_dict()
            return result
        if command == "doctor":
            validation = self.manager.validate()
            listing = self.manager.list_plugins()
            return {
                "status": "success" if validation.get("status") == "success" and listing.get("status") == "success" else "failed",
                "checks": {
                    "repository": validation,
                    "listing": {
                        "status": listing.get("status"),
                        "plugin_count": listing.get("plugin_count", 0),
                    },
                },
            }
        return self.manager.list_plugins()


def render_result(result: dict[str, Any], json_output: bool = False) -> str:
    if json_output:
        return json.dumps(result, ensure_ascii=False, indent=2)

    status = result.get("status", "unknown")
    lines = ["NTPE Plugin Marketplace CLI", "=============================", f"status: {status}"]
    if "plugin_id" in result:
        lines.append(f"plugin_id: {result['plugin_id']}")
    if "plugin_count" in result:
        lines.append(f"plugin_count: {result['plugin_count']}")
    if result.get("error"):
        lines.append(f"error: {result['error']}")
    if result.get("errors"):
        lines.append("errors: " + "; ".join(str(item) for item in result["errors"]))
    if result.get("missing_dependencies"):
        lines.append("missing_dependencies: " + ", ".join(result["missing_dependencies"]))
    if "plugins" in result:
        for item in result["plugins"]:
            lines.append(f"- {item.get('plugin_id')} {item.get('version')} {item.get('name')}")
    return "\n".join(lines)


def run_cli(argv: Sequence[str] | None = None, default_root: str | Path | None = None) -> int:
    parser = PluginMarketplaceCLI.build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root) if args.root else Path(default_root or Path.cwd())
    cli = PluginMarketplaceCLI(root=root, ntpe_version=args.ntpe_version)
    result = cli.execute(args)
    print(render_result(result, json_output=args.json))
    return 0 if result.get("status") == "success" else 1
