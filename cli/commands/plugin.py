from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .manifest import attach_plugin_manifest
from .plugin_store import CLIPluginStore


def _store(context: CLIContext, args: object) -> CLIPluginStore:
    plugin_dir = getattr(args, "plugin_dir", None) or ".ntpe_plugins"
    return CLIPluginStore(context.root, plugin_dir=plugin_dir)


def _success(message: str, payload: Dict[str, Any]) -> CLIResult:
    attach_plugin_manifest(payload)
    return CLIResult.success(message, **payload)


def command_plugin(context: CLIContext, args: object) -> CLIResult:
    try:
        action = getattr(args, "plugin_action", None) or "list"
        store = _store(context, args)

        if action == "list":
            enabled_value = getattr(args, "enabled", None)
            if bool(getattr(args, "disabled", False)):
                enabled_value = False
            plugins = store.list(enabled=enabled_value)
            return _success("Plugin list", {"plugins": plugins, "store": store.manifest()})

        if action == "info":
            name = getattr(args, "name")
            plugin = store.info(name)
            if not plugin:
                return CLIResult.failure(f"Plugin not found: {name}", exit_code=2)
            return _success("Plugin info", {"plugin": plugin, "store": store.manifest()})

        if action == "enable":
            plugin = store.enable(getattr(args, "name"), True)
            return _success("Plugin enabled", {"plugin": plugin, "store": store.manifest()})

        if action == "disable":
            plugin = store.disable(getattr(args, "name"))
            return _success("Plugin disabled", {"plugin": plugin, "store": store.manifest()})

        if action == "install":
            package = Path(getattr(args, "package"))
            if not package.is_absolute():
                package = context.root / package
            plugin = store.install(package, replace=bool(getattr(args, "replace", False)))
            return _success("Plugin installed", {"plugin": plugin, "store": store.manifest()})

        if action == "uninstall":
            plugin = store.uninstall(getattr(args, "name"))
            return _success("Plugin uninstalled", {"plugin": plugin, "store": store.manifest()})

        if action == "validate":
            validation = store.validate(getattr(args, "name", None))
            payload = {"validation": validation.to_dict(), "store": store.manifest()}
            attach_plugin_manifest(payload)
            if not validation.valid:
                return CLIResult.failure("Plugin validation failed", exit_code=2, errors=validation.errors, **payload)
            return CLIResult.success("Plugin valid", **payload)

        return CLIResult.failure(f"Unknown plugin action: {action}", exit_code=2)
    except Exception as exc:
        return CLIResult.failure(f"Plugin command failed: {exc}", exit_code=2)


def register_plugin_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("plugin", "manage NTPE plugins", command_plugin))
    return registry


__all__ = ["command_plugin", "register_plugin_command"]
