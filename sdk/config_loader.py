"""Load and save Stage-07.6 SDK configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .config import SDKConfig
from .config_validator import SDKConfigValidator


class SDKConfigLoader:
    def __init__(self, validator: SDKConfigValidator | None = None):
        self.validator = validator or SDKConfigValidator()

    def loads(self, payload: str, *, validate: bool = True) -> SDKConfig:
        config = SDKConfig.from_dict(json.loads(payload))
        if validate:
            self.validator.assert_valid(config)
        return config

    def dumps(self, config: SDKConfig, *, include_secrets: bool = False, indent: int = 2) -> str:
        self.validator.assert_valid(config)
        return json.dumps(config.to_dict(include_secrets=include_secrets), ensure_ascii=False, indent=indent)

    def load(self, path: str | Path, *, validate: bool = True) -> SDKConfig:
        return self.loads(Path(path).read_text(encoding="utf-8"), validate=validate)

    def save(self, config: SDKConfig, path: str | Path, *, include_secrets: bool = False) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.dumps(config, include_secrets=include_secrets), encoding="utf-8")
        return target

    def from_dict(self, data: Dict[str, Any], *, validate: bool = True) -> SDKConfig:
        config = SDKConfig.from_dict(data)
        if validate:
            self.validator.assert_valid(config)
        return config


def load_config(path: str | Path, *, validate: bool = True) -> SDKConfig:
    return SDKConfigLoader().load(path, validate=validate)


def save_config(config: SDKConfig, path: str | Path, *, include_secrets: bool = False) -> Path:
    return SDKConfigLoader().save(config, path, include_secrets=include_secrets)
