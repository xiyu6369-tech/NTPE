from __future__ import annotations

import json
from pathlib import Path


class ConfigError(Exception):
    pass


class ConfigManager:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2]
        self.default_path = self.root / "config" / "default_config.json"
        self.local_path = self.root / "config" / "config.json"
        self.data = self._load()

    def _load_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def _load(self) -> dict:
        default = self._load_json(self.default_path)
        local = self._load_json(self.local_path)
        merged = self._deep_merge(default, local)
        self._validate(merged)
        return merged

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)

        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _validate(self, data: dict) -> None:
        pipeline = data.get("pipeline", {})

        for key in ["timeout", "rpm_limit", "chunk_size", "context_size"]:
            value = pipeline.get(key)
            if value is None:
                raise ConfigError(f"Missing pipeline.{key}")
            if not isinstance(value, int) or value <= 0:
                raise ConfigError(f"pipeline.{key} must be a positive integer")

        translation = data.get("translation", {})
        if not translation.get("provider"):
            raise ConfigError("Missing translation.provider")
        if not translation.get("model"):
            raise ConfigError("Missing translation.model")
        if not translation.get("target_language"):
            raise ConfigError("Missing translation.target_language")

    @property
    def app_name(self) -> str:
        return self.data["app"]["name"]

    @property
    def version(self) -> str:
        return self.data["app"]["version"]

    @property
    def provider(self) -> str:
        return self.data["translation"]["provider"]

    @property
    def model(self) -> str:
        return self.data["translation"]["model"]

    @property
    def target_language(self) -> str:
        return self.data["translation"]["target_language"]

    @property
    def timeout(self) -> int:
        return self.data["pipeline"]["timeout"]

    @property
    def rpm_limit(self) -> int:
        return self.data["pipeline"]["rpm_limit"]

    @property
    def chunk_size(self) -> int:
        return self.data["pipeline"]["chunk_size"]

    @property
    def context_size(self) -> int:
        return self.data["pipeline"]["context_size"]

    @property
    def api_key(self) -> str:
        return self.data.get("user", {}).get("api_key", "")

    def get(self, path: str, default=None):
        current = self.data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current