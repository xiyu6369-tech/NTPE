"""Stage-07.7 SDK Plugin API manifest support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SDK_PLUGIN_VERSION = "0.7.7"
SDK_PLUGIN_STAGE = "NTPE 1.0 Beta Stage-07.7 SDK Plugin API"


@dataclass
class PluginManifest:
    name: str
    version: str = "1.0.0"
    entrypoint: Optional[str] = None
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            name=str(data.get("name", "")),
            version=str(data.get("version", "1.0.0")),
            entrypoint=data.get("entrypoint"),
            description=str(data.get("description", "")),
            capabilities=list(data.get("capabilities", [])),
            metadata=dict(data.get("metadata", {})),
        )


def build_sdk_plugin_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Plugin API",
        "stage": SDK_PLUGIN_STAGE,
        "version": SDK_PLUGIN_VERSION,
        "status": "beta",
        "components": [
            "SDKPlugin",
            "SDKPluginManager",
            "SDKPluginRegistry",
            "SDKPluginContext",
            "SDKPluginLoader",
            "PluginManifest",
            "PluginDescriptor",
            "PluginResult",
        ],
        "capabilities": [
            "plugin_base_interface",
            "plugin_registry",
            "plugin_manager",
            "plugin_context",
            "plugin_lifecycle",
            "plugin_manifest",
            "plugin_discovery",
            "runtime_plugin_bridge",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "Stage-06.9 CLI Freeze compatible",
        "sdk_core_compatibility": "Stage-07.0 SDK Core compatible",
        "sdk_session_compatibility": "Stage-07.1 SDK Session API compatible",
        "sdk_translation_compatibility": "Stage-07.2 SDK Translation API compatible",
        "sdk_batch_compatibility": "Stage-07.3 SDK Batch API compatible",
        "sdk_streaming_compatibility": "Stage-07.4 SDK Streaming API compatible",
        "sdk_error_compatibility": "Stage-07.5 SDK Error Handling API compatible",
        "sdk_config_compatibility": "Stage-07.6 SDK Configuration API compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
