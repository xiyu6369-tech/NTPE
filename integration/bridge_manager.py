"""SDK-CLI bridge manager for NTPE Stage-08.2."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .bridge_models import BridgeResult
from .sdk_cli_bridge import SDKCLIBridge


class BridgeManager:
    version = "0.8.2"

    def __init__(self, *, bridge: Optional[SDKCLIBridge] = None) -> None:
        self.bridge = bridge or SDKCLIBridge()

    def attach_sdk(self, sdk_client: Any, **metadata: Any) -> str:
        return self.bridge.register_sdk(sdk_client, metadata=metadata)

    def attach_cli(self, cli_adapter: Any, **metadata: Any) -> str:
        return self.bridge.register_cli(cli_adapter, metadata=metadata)

    def attach_runtime(self, runtime: Any, **metadata: Any) -> str:
        return self.bridge.register_runtime(runtime, metadata=metadata)

    def create_session(self, session_id: str, **metadata: Any) -> Dict[str, Any]:
        return self.bridge.create_session(session_id, **metadata)

    def sdk_command(self, action: str, **payload: Any) -> BridgeResult:
        return self.bridge.cli_to_sdk(action, **payload)

    def cli_command(self, action: str, **payload: Any) -> BridgeResult:
        return self.bridge.sdk_to_cli(action, **payload)

    def runtime_command(self, action: str, **payload: Any) -> BridgeResult:
        return self.bridge.route("runtime", action, **payload)

    def manifest(self) -> Dict[str, Any]:
        manifest = self.bridge.manifest()
        manifest["manager_version"] = self.version
        return manifest
