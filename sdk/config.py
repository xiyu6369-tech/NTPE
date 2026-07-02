"""Stage-07.6 SDK Configuration API."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .config_models import BatchConfig, ProviderConfig, RuntimeConfig, StreamingConfig, TranslationConfig

SDK_CONFIG_VERSION = "0.7.6"
SDK_CONFIG_STAGE = "NTPE 1.0 Beta Stage-07.6 SDK Configuration API"


@dataclass
class SDKConfig:
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = SDK_CONFIG_VERSION

    def to_dict(self, *, include_secrets: bool = False) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": SDK_CONFIG_STAGE,
            "provider": self.provider.to_dict(include_secrets=include_secrets),
            "runtime": self.runtime.to_dict(),
            "translation": self.translation.to_dict(),
            "batch": self.batch.to_dict(),
            "streaming": self.streaming.to_dict(),
            "metadata": dict(self.metadata),
            "backward_compatible": True,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SDKConfig":
        return cls(
            provider=ProviderConfig.from_dict(dict(data.get("provider", {}))),
            runtime=RuntimeConfig.from_dict(dict(data.get("runtime", {}))),
            translation=TranslationConfig.from_dict(dict(data.get("translation", {}))),
            batch=BatchConfig.from_dict(dict(data.get("batch", {}))),
            streaming=StreamingConfig.from_dict(dict(data.get("streaming", {}))),
            metadata=dict(data.get("metadata", {})),
            version=str(data.get("version", SDK_CONFIG_VERSION)),
        )

    def to_translation_options(self) -> Dict[str, Any]:
        return {
            "source_language": self.translation.source_language,
            "target_language": self.translation.target_language,
            "model": self.provider.model,
            "metadata": {"sdk_config_version": self.version, **dict(self.translation.metadata)},
        }

    def to_runtime_payload(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.to_dict(),
            "runtime": self.runtime.to_dict(),
            "translation": self.translation.to_dict(),
            "batch": self.batch.to_dict(),
            "streaming": self.streaming.to_dict(),
            "sdk": {"version": self.version, "stage": SDK_CONFIG_STAGE},
        }

    def merge_metadata(self, **metadata: Any) -> "SDKConfig":
        self.metadata.update(metadata)
        return self


def default_config(metadata: Optional[Dict[str, Any]] = None) -> SDKConfig:
    cfg = SDKConfig(metadata=dict(metadata or {}))
    return cfg


def build_sdk_config_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Configuration API",
        "stage": SDK_CONFIG_STAGE,
        "version": SDK_CONFIG_VERSION,
        "status": "beta",
        "components": [
            "SDKConfig",
            "SDKConfigBuilder",
            "SDKConfigLoader",
            "SDKConfigValidator",
            "ProviderConfig",
            "RuntimeConfig",
            "TranslationConfig",
            "BatchConfig",
            "StreamingConfig",
        ],
        "capabilities": [
            "configuration_builder",
            "configuration_validation",
            "json_serialization",
            "provider_configuration",
            "runtime_configuration",
            "translation_configuration",
            "batch_configuration",
            "streaming_configuration",
            "runtime_payload_export",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "Stage-06.9 CLI Freeze compatible",
        "sdk_core_compatibility": "Stage-07.0 SDK Core compatible",
        "sdk_session_compatibility": "Stage-07.1 SDK Session API compatible",
        "sdk_translation_compatibility": "Stage-07.2 SDK Translation API compatible",
        "sdk_batch_compatibility": "Stage-07.3 SDK Batch API compatible",
        "sdk_streaming_compatibility": "Stage-07.4 SDK Streaming API compatible",
        "sdk_error_compatibility": "Stage-07.5 SDK Error Handling API compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
