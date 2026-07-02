"""Stage-07.6 SDK configuration data models.

Additive configuration objects for SDK integrations. These models do not change
Foundation, Runtime, CLI, or earlier SDK contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProviderConfig:
    name: str = "default"
    model: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    timeout_seconds: int = 120
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_secrets: bool = False) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "model": self.model,
            "endpoint": self.endpoint,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "metadata": dict(self.metadata),
        }
        data["api_key"] = self.api_key if include_secrets else ("***" if self.api_key else None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        return cls(
            name=str(data.get("name", "default")),
            model=data.get("model"),
            api_key=data.get("api_key"),
            endpoint=data.get("endpoint"),
            timeout_seconds=int(data.get("timeout_seconds", 120)),
            max_retries=int(data.get("max_retries", 3)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class RuntimeConfig:
    work_dir: Optional[str] = None
    cache_dir: Optional[str] = None
    log_level: str = "INFO"
    resume_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_dir": self.work_dir,
            "cache_dir": self.cache_dir,
            "log_level": self.log_level,
            "resume_enabled": self.resume_enabled,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        return cls(
            work_dir=data.get("work_dir"),
            cache_dir=data.get("cache_dir"),
            log_level=str(data.get("log_level", "INFO")),
            resume_enabled=bool(data.get("resume_enabled", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class TranslationConfig:
    source_language: str = "ko"
    target_language: str = "zh-TW"
    chunk_size: int = 3000
    preserve_formatting: bool = True
    quality_check: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "chunk_size": self.chunk_size,
            "preserve_formatting": self.preserve_formatting,
            "quality_check": self.quality_check,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranslationConfig":
        return cls(
            source_language=str(data.get("source_language", "ko")),
            target_language=str(data.get("target_language", "zh-TW")),
            chunk_size=int(data.get("chunk_size", 3000)),
            preserve_formatting=bool(data.get("preserve_formatting", True)),
            quality_check=bool(data.get("quality_check", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class BatchConfig:
    continue_on_error: bool = True
    max_workers: int = 1
    output_suffix: str = "_zh"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "continue_on_error": self.continue_on_error,
            "max_workers": self.max_workers,
            "output_suffix": self.output_suffix,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchConfig":
        return cls(
            continue_on_error=bool(data.get("continue_on_error", True)),
            max_workers=int(data.get("max_workers", 1)),
            output_suffix=str(data.get("output_suffix", "_zh")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class StreamingConfig:
    emit_tokens: bool = True
    emit_segments: bool = True
    callback_errors: str = "raise"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emit_tokens": self.emit_tokens,
            "emit_segments": self.emit_segments,
            "callback_errors": self.callback_errors,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingConfig":
        return cls(
            emit_tokens=bool(data.get("emit_tokens", True)),
            emit_segments=bool(data.get("emit_segments", True)),
            callback_errors=str(data.get("callback_errors", "raise")),
            metadata=dict(data.get("metadata", {})),
        )
