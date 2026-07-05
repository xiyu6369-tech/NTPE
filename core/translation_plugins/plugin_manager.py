from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .plugin import PluginContext, PluginResult, TranslationPlugin, TranslationPluginProtocol
from .registry import TranslationPluginRegistry


OFFICIAL_PLUGIN_KINDS: tuple[str, ...] = (
    "prompt",
    "glossary",
    "character_memory",
    "context",
    "provider",
    "qa",
    "formatter",
    "output",
)


class TranslationPluginManager:
    """Official plugin manager for NTPE 1.2 Professional Stage-08.

    Plugins extend the Runtime/Resource/Pipeline stack without replacing it.
    The manager can execute a single plugin or a deterministic chain of plugin
    kinds while preserving the payload contract used by Stage-06/07.
    """

    version = "1.2-professional-stage-08"
    compatibility_floor = "1.1-lts-stable"

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.registry = TranslationPluginRegistry()
        self._load_official_defaults()

    @property
    def plugin_dir(self) -> Path:
        return self.root / ".ntpe_plugins"

    def register(self, plugin: TranslationPluginProtocol, replace: bool = False) -> TranslationPluginProtocol:
        return self.registry.register(plugin, replace=replace)

    def register_default(self, kind: str, name: str = "default", replace: bool = False, **metadata: Any) -> TranslationPlugin:
        return self.registry.register_default(kind=kind, name=name, replace=replace, **metadata)

    def get(self, kind: str, name: str = "default") -> dict[str, Any] | None:
        plugin = self.registry.get(kind, name)
        if plugin is None:
            return None
        return plugin.to_dict() if hasattr(plugin, "to_dict") else {
            "name": plugin.name,
            "kind": plugin.kind,
            "version": getattr(plugin, "version", "unknown"),
            "enabled": bool(getattr(plugin, "enabled", True)),
            "metadata": {},
        }

    def describe(self) -> dict[str, Any]:
        return {
            "status": "success",
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "plugin_count": len(self.registry.keys()),
            "plugins": self.registry.list(),
        }

    def validate(self) -> dict[str, Any]:
        missing = [kind for kind in OFFICIAL_PLUGIN_KINDS if self.registry.get(kind, "default") is None]
        disabled = [f"{item['kind']}:{item['name']}" for item in self.registry.list() if not item.get("enabled", True)]
        return {
            "status": "success" if not missing else "failed",
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "missing": missing,
            "disabled": disabled,
            "plugin_count": len(self.registry.keys()),
        }

    def execute(self, kind: str, name: str = "default", payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        plugin = self.registry.require(kind, name)
        context = PluginContext(stage=kind, payload=dict(payload or {}), metadata=dict(metadata or {}))
        try:
            result = plugin.execute(context)
            if not isinstance(result, PluginResult):
                result = PluginResult(status=result.get("status", "success"), payload=dict(result.get("payload", result)), metadata=dict(result.get("metadata", {})), error=result.get("error"))
        except Exception as exc:
            result = PluginResult(status="failed", payload=dict(payload or {}), metadata={"plugin": name, "kind": kind}, error=str(exc))
        return result.to_dict()

    def execute_chain(self, kinds: list[str] | tuple[str, ...] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        kinds = tuple(kinds or OFFICIAL_PLUGIN_KINDS)
        current_payload = dict(payload or {})
        results: list[dict[str, Any]] = []
        for kind in kinds:
            result = self.execute(kind, payload=current_payload)
            results.append({"kind": kind, **result})
            if result.get("status") == "failed":
                return {"status": "failed", "version": self.version, "results": results, "payload": current_payload}
            current_payload.update(result.get("payload", {}))
        return {"status": "success", "version": self.version, "results": results, "payload": current_payload}

    def save_manifest(self, manifest_id: str | None = None) -> dict[str, Any]:
        manifest_id = manifest_id or uuid4().hex
        path = self.plugin_dir / manifest_id / "plugin_manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        payload = {
            "manifest_id": manifest_id,
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "plugins": self.registry.list(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "success", "manifest_id": manifest_id, "manifest_path": str(path), "manifest": payload}

    def _load_official_defaults(self) -> None:
        for kind in OFFICIAL_PLUGIN_KINDS:
            self.register_default(kind, "default", role=f"translation_{kind}_plugin")
