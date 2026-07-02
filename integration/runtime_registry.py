"""Runtime registry for NTPE Stage-08.1."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .runtime_models import RuntimeMetadata


class RuntimeRegistry:
    def __init__(self) -> None:
        self._instances: Dict[str, Any] = {}
        self._metadata: Dict[str, RuntimeMetadata] = {}

    def register(self, runtime: Any, *, name: str = "runtime", version: Optional[str] = None, metadata: Optional[dict] = None) -> RuntimeMetadata:
        item = RuntimeMetadata.create(name=name, version=str(version or getattr(runtime, "version", "1.0")), metadata=metadata)
        self._instances[item.runtime_id] = runtime
        self._metadata[item.runtime_id] = item
        return item

    def get(self, runtime_id: str) -> Optional[Any]:
        return self._instances.get(runtime_id)

    def require(self, runtime_id: str) -> Any:
        runtime = self.get(runtime_id)
        if runtime is None:
            raise KeyError(f"runtime not registered: {runtime_id}")
        return runtime

    def metadata(self, runtime_id: str) -> Optional[RuntimeMetadata]:
        return self._metadata.get(runtime_id)

    def require_metadata(self, runtime_id: str) -> RuntimeMetadata:
        metadata = self.metadata(runtime_id)
        if metadata is None:
            raise KeyError(f"runtime metadata not registered: {runtime_id}")
        return metadata

    def active(self) -> Iterable[RuntimeMetadata]:
        return tuple(self._metadata.values())

    def manifest(self) -> Dict[str, Any]:
        return {"count": len(self._metadata), "runtimes": [item.to_dict() for item in self.active()]}
