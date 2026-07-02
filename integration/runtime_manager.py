"""Runtime manager for NTPE Stage-08.1."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .runtime_bridge import RuntimeBridge
from .runtime_models import RuntimeExecutionResult


class RuntimeManager:
    version = "0.8.1"

    def __init__(self, *, bridge: Optional[RuntimeBridge] = None) -> None:
        self.bridge = bridge or RuntimeBridge()

    def create(self, runtime: Any, *, name: str = "runtime", metadata: Optional[Dict[str, Any]] = None) -> str:
        return self.bridge.attach(runtime, name=name, metadata=metadata)

    def start(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        return self.bridge.start(runtime_id, **payload)

    def execute(self, runtime_id: str, action: str = "execute", **payload: Any) -> RuntimeExecutionResult:
        return self.bridge.execute(runtime_id, action=action, **payload)

    def resume(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        return self.bridge.resume(runtime_id, **payload)

    def stop(self, runtime_id: str, **payload: Any) -> RuntimeExecutionResult:
        return self.bridge.stop(runtime_id, **payload)

    def shutdown(self, runtime_id: str) -> RuntimeExecutionResult:
        return self.stop(runtime_id, reason="shutdown")

    def status(self, runtime_id: str) -> Dict[str, Any]:
        metadata = self.bridge.registry.require_metadata(runtime_id)
        runtime = self.bridge.registry.require(runtime_id)
        runtime_status = runtime.status() if hasattr(runtime, "status") else {"status": metadata.status}
        return {"metadata": metadata.to_dict(), "runtime": runtime_status}

    def manifest(self) -> Dict[str, Any]:
        manifest = self.bridge.manifest()
        manifest["manager_version"] = self.version
        return manifest
