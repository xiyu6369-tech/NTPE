"""Extension registry for NTPE Stage-08.4."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .extension_models import ExtensionDescriptor, ExtensionManifest


class ExtensionRegistry:
    version = "0.8.4"

    def __init__(self) -> None:
        self._extensions: Dict[str, Any] = {}
        self._descriptors: Dict[str, ExtensionDescriptor] = {}

    def register(self, extension: Any, *, manifest: Optional[ExtensionManifest | Dict[str, Any]] = None, name: Optional[str] = None, source: str = "integration", replace: bool = False, metadata: Optional[Dict[str, Any]] = None) -> ExtensionDescriptor:
        ext_manifest = self._coerce_manifest(extension, manifest, name=name, metadata=metadata)
        ext_manifest.validate()
        ext_name = ext_manifest.name
        if ext_name in self._extensions and not replace:
            raise ValueError(f"extension already registered: {ext_name}")
        descriptor = ExtensionDescriptor(ext_manifest, source=source)
        self._extensions[ext_name] = extension
        self._descriptors[ext_name] = descriptor
        return descriptor

    def _coerce_manifest(self, extension: Any, manifest: Optional[ExtensionManifest | Dict[str, Any]], *, name: Optional[str], metadata: Optional[Dict[str, Any]]) -> ExtensionManifest:
        if isinstance(manifest, ExtensionManifest):
            result = manifest
        elif isinstance(manifest, dict):
            result = ExtensionManifest(**manifest)
        else:
            raw = getattr(extension, "manifest", None)
            if isinstance(raw, ExtensionManifest):
                result = raw
            elif isinstance(raw, dict):
                result = ExtensionManifest(**raw)
            else:
                result = ExtensionManifest(
                    name=name or getattr(extension, "name", extension.__class__.__name__),
                    version=str(getattr(extension, "version", "1.0.0")),
                    entrypoint=str(getattr(extension, "entrypoint", extension.__class__.__name__)),
                    capabilities=list(getattr(extension, "capabilities", []) or []),
                    kind=str(getattr(extension, "kind", "extension")),
                )
        if metadata:
            merged = dict(result.metadata)
            merged.update(metadata)
            result.metadata = merged
        return result

    def unregister(self, name: str) -> Optional[Any]:
        self._descriptors.pop(name, None)
        return self._extensions.pop(name, None)

    def get(self, name: str) -> Optional[Any]:
        return self._extensions.get(name)

    def require(self, name: str) -> Any:
        extension = self.get(name)
        if extension is None:
            raise KeyError(f"extension not registered: {name}")
        return extension

    def descriptor(self, name: str) -> ExtensionDescriptor:
        if name not in self._descriptors:
            raise KeyError(f"extension descriptor not registered: {name}")
        return self._descriptors[name]

    def names(self) -> List[str]:
        return sorted(self._extensions.keys())

    def discover(self, capability: Optional[str] = None) -> List[ExtensionDescriptor]:
        values = list(self._descriptors.values())
        if capability is None:
            return values
        return [item for item in values if capability in item.capabilities]

    def mark(self, name: str, status: str) -> None:
        self.descriptor(name).mark(status)

    def manifest(self) -> Dict[str, Any]:
        return {"version": self.version, "count": len(self._descriptors), "extensions": [item.to_dict() for item in self.discover()]}

    def __iter__(self) -> Iterable[Any]:
        return iter(self._extensions.values())
