"""Extension loader for NTPE Stage-08.4."""
from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

from .extension_models import ExtensionManifest


class ExtensionLoader:
    version = "0.8.4"

    def load_from_manifest(self, manifest: ExtensionManifest | Dict[str, Any]) -> Any:
        manifest_obj = manifest if isinstance(manifest, ExtensionManifest) else ExtensionManifest(**manifest)
        manifest_obj.validate()
        if not manifest_obj.entrypoint or ":" not in manifest_obj.entrypoint:
            raise ValueError("extension manifest entrypoint must use module:attribute")
        module_name, attribute = manifest_obj.entrypoint.split(":", 1)
        module = import_module(module_name)
        factory = getattr(module, attribute)
        return factory() if callable(factory) else factory

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "supports": ["module:attribute"]}
