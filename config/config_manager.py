"""
NTPE - Novel Translator Professional Edition
Version : 0.1.0 Alpha
File    : config/config_manager.py
Purpose : Load and create application configuration.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manage NTPE configuration files."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.config_dir = self.project_root / "config"
        self.default_config_path = self.config_dir / "default_config.json"
        self.config_path = self.config_dir / "config.json"

    def load_or_create(self) -> dict[str, Any]:
        """Load config.json, or create it from default_config.json."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if not self.default_config_path.exists():
            raise FileNotFoundError(f"Missing default config: {self.default_config_path}")

        if not self.config_path.exists():
            shutil.copyfile(self.default_config_path, self.config_path)

        with self.config_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("config.json must contain a JSON object.")

        return data
