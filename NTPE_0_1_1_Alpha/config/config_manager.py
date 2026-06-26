"""Configuration manager for NTPE.

This module loads the default configuration and creates a user-editable
configuration file under `user_data/config.json` when it does not exist.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from core.exceptions import ConfigError


class ConfigManager:
    """Load and access NTPE configuration values."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.default_config_path = project_root / "config" / "default_config.json"
        self.user_config_path = project_root / "user_data" / "config.json"
        self._config: dict[str, Any] = {}

    def ensure_user_config(self) -> None:
        """Create user config from default config if needed."""
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.default_config_path.exists():
            raise ConfigError(f"Default config not found: {self.default_config_path}")

        if not self.user_config_path.exists():
            shutil.copyfile(self.default_config_path, self.user_config_path)

    def load(self) -> dict[str, Any]:
        """Load and return the current user configuration."""
        self.ensure_user_config()

        try:
            with self.user_config_path.open("r", encoding="utf-8") as file:
                self._config = json.load(file)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON config: {self.user_config_path}") from exc
        except OSError as exc:
            raise ConfigError(f"Unable to read config: {self.user_config_path}") from exc

        return self._config

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Read config by dotted path, such as `api.nvidia.rpm_limit`."""
        if not self._config:
            self.load()

        current: Any = self._config
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current
