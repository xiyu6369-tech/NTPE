"""Fluent builder for Stage-07.6 SDK configuration."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .config import SDKConfig


class SDKConfigBuilder:
    def __init__(self, base: Optional[SDKConfig] = None):
        self._config = base or SDKConfig()

    def provider(self, *, name: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout_seconds: Optional[int] = None, max_retries: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> "SDKConfigBuilder":
        if name is not None:
            self._config.provider.name = name
        if model is not None:
            self._config.provider.model = model
        if api_key is not None:
            self._config.provider.api_key = api_key
        if endpoint is not None:
            self._config.provider.endpoint = endpoint
        if timeout_seconds is not None:
            self._config.provider.timeout_seconds = timeout_seconds
        if max_retries is not None:
            self._config.provider.max_retries = max_retries
        if metadata:
            self._config.provider.metadata.update(metadata)
        return self

    def runtime(self, *, work_dir: Optional[str] = None, cache_dir: Optional[str] = None, log_level: Optional[str] = None, resume_enabled: Optional[bool] = None, metadata: Optional[Dict[str, Any]] = None) -> "SDKConfigBuilder":
        if work_dir is not None:
            self._config.runtime.work_dir = work_dir
        if cache_dir is not None:
            self._config.runtime.cache_dir = cache_dir
        if log_level is not None:
            self._config.runtime.log_level = log_level
        if resume_enabled is not None:
            self._config.runtime.resume_enabled = resume_enabled
        if metadata:
            self._config.runtime.metadata.update(metadata)
        return self

    def translation(self, *, source_language: Optional[str] = None, target_language: Optional[str] = None, chunk_size: Optional[int] = None, preserve_formatting: Optional[bool] = None, quality_check: Optional[bool] = None, metadata: Optional[Dict[str, Any]] = None) -> "SDKConfigBuilder":
        if source_language is not None:
            self._config.translation.source_language = source_language
        if target_language is not None:
            self._config.translation.target_language = target_language
        if chunk_size is not None:
            self._config.translation.chunk_size = chunk_size
        if preserve_formatting is not None:
            self._config.translation.preserve_formatting = preserve_formatting
        if quality_check is not None:
            self._config.translation.quality_check = quality_check
        if metadata:
            self._config.translation.metadata.update(metadata)
        return self

    def batch(self, *, continue_on_error: Optional[bool] = None, max_workers: Optional[int] = None, output_suffix: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> "SDKConfigBuilder":
        if continue_on_error is not None:
            self._config.batch.continue_on_error = continue_on_error
        if max_workers is not None:
            self._config.batch.max_workers = max_workers
        if output_suffix is not None:
            self._config.batch.output_suffix = output_suffix
        if metadata:
            self._config.batch.metadata.update(metadata)
        return self

    def streaming(self, *, emit_tokens: Optional[bool] = None, emit_segments: Optional[bool] = None, callback_errors: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> "SDKConfigBuilder":
        if emit_tokens is not None:
            self._config.streaming.emit_tokens = emit_tokens
        if emit_segments is not None:
            self._config.streaming.emit_segments = emit_segments
        if callback_errors is not None:
            self._config.streaming.callback_errors = callback_errors
        if metadata:
            self._config.streaming.metadata.update(metadata)
        return self

    def metadata(self, **metadata: Any) -> "SDKConfigBuilder":
        self._config.metadata.update(metadata)
        return self

    def build(self) -> SDKConfig:
        return SDKConfig.from_dict(self._config.to_dict(include_secrets=True))


def config_builder(base: Optional[SDKConfig] = None) -> SDKConfigBuilder:
    return SDKConfigBuilder(base)
