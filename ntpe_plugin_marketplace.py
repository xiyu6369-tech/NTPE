# =====================================================
# NTPE 1.2 Professional Stage-11
# Plugin Marketplace CLI Compatibility Entrypoint
# =====================================================

from __future__ import annotations

import argparse
from pathlib import Path

from core.translation_plugins.marketplace import PluginMarketplaceManager

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="NTPE Plugin Marketplace")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list")
    sub.add_parser("validate")
    install_parser = sub.add_parser("install")
    install_parser.add_argument("package")
    install_parser.add_argument("--replace", action="store_true")
    uninstall_parser = sub.add_parser("uninstall")
    uninstall_parser.add_argument("plugin_id")
    args = parser.parse_args()

    manager = PluginMarketplaceManager(ROOT)
    if args.command == "install":
        result = manager.install(args.package, replace=args.replace)
    elif args.command == "uninstall":
        result = manager.uninstall(args.plugin_id)
    elif args.command == "validate":
        result = manager.validate()
    else:
        result = manager.list_plugins()
    print(result)
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
