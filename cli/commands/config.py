from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .config_store import CLIConfigStore, parse_config_value
from .manifest import attach_config_manifest


def _store(context: CLIContext, args: object) -> CLIConfigStore:
    config_dir = getattr(args, "config_dir", None) or ".ntpe"
    return CLIConfigStore(context.root, config_dir=config_dir)


def _result(message: str, payload: Dict[str, Any]) -> CLIResult:
    attach_config_manifest(payload)
    return CLIResult.success(message, **payload)


def command_config(context: CLIContext, args: object) -> CLIResult:
    try:
        action = getattr(args, "config_action", None) or "list"
        store = _store(context, args)

        if action == "list":
            data = store.load()
            return _result("Config list", {"config": data, "settings": data.get("settings", {}), "store": store.manifest()})

        if action == "get":
            key = getattr(args, "key", None)
            value = store.get(key)
            return _result("Config value", {"key": key, "value": value, "store": store.manifest()})

        if action == "set":
            key = getattr(args, "key")
            raw = getattr(args, "value")
            value = parse_config_value(raw)
            data = store.set(key, value)
            return _result("Config set", {"key": key, "value": value, "config": data, "store": store.manifest()})

        if action == "validate":
            validation = store.validate()
            validation["store"] = store.manifest()
            if not validation["valid"]:
                attach_config_manifest(validation)
                return CLIResult.failure("Config validation failed", exit_code=2, errors=validation["errors"], **validation)
            return _result("Config valid", validation)

        if action == "export":
            output = Path(getattr(args, "output", None) or "ntpe_config_export.json")
            exported = store.export(context.root / output if not output.is_absolute() else output)
            exported["store"] = store.manifest()
            return _result("Config exported", exported)

        if action == "import":
            package = Path(getattr(args, "package"))
            imported = store.import_file(context.root / package if not package.is_absolute() else package, replace=bool(getattr(args, "replace", False)))
            return _result("Config imported", {"config": imported, "store": store.manifest()})

        if action == "reset":
            data = store.reset()
            return _result("Config reset", {"config": data, "settings": data.get("settings", {}), "store": store.manifest()})

        return CLIResult.failure(f"Unknown config action: {action}", exit_code=2)
    except Exception as exc:
        return CLIResult.failure(f"Config command failed: {exc}", exit_code=2)


def register_config_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("config", "manage NTPE configuration", command_config))
    return registry


__all__ = ["command_config", "register_config_command"]
