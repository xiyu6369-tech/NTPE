"""Validation helpers for Stage-07.6 SDK configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .config import SDKConfig


@dataclass
class SDKConfigValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings)}


class SDKConfigValidator:
    VALID_CALLBACK_ERROR_POLICIES = {"raise", "ignore", "record"}

    def validate(self, config: SDKConfig) -> SDKConfigValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        if not config.provider.name:
            errors.append("provider.name is required")
        if config.provider.timeout_seconds <= 0:
            errors.append("provider.timeout_seconds must be positive")
        if config.provider.max_retries < 0:
            errors.append("provider.max_retries must be zero or positive")
        if not config.translation.source_language:
            errors.append("translation.source_language is required")
        if not config.translation.target_language:
            errors.append("translation.target_language is required")
        if config.translation.chunk_size <= 0:
            errors.append("translation.chunk_size must be positive")
        if config.batch.max_workers <= 0:
            errors.append("batch.max_workers must be positive")
        if config.streaming.callback_errors not in self.VALID_CALLBACK_ERROR_POLICIES:
            errors.append("streaming.callback_errors must be one of: ignore, raise, record")
        if not config.provider.model:
            warnings.append("provider.model is not set")
        return SDKConfigValidationResult(ok=not errors, errors=errors, warnings=warnings)

    def assert_valid(self, config: SDKConfig) -> SDKConfig:
        result = self.validate(config)
        if not result.ok:
            raise ValueError("; ".join(result.errors))
        return config


def validate_config(config: SDKConfig) -> SDKConfigValidationResult:
    return SDKConfigValidator().validate(config)
