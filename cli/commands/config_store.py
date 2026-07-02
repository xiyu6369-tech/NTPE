from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "mock",
    "quality": "standard",
    "runtime": {
        "checkpoint_interval": 1,
        "resume": True,
    },
    "session": {
        "session_dir": "sessions",
    },
    "benchmark": {
        "enabled": True,
        "output": "benchmark_reports",
    },
    "translation": {
        "suffix": "_zh",
        "pattern": "*.txt",
    },
}


@dataclass
class CLIConfigStore:
    """JSON-backed configuration store for NTPE CLI.

    This layer belongs to the Beta CLI application layer. It does not modify
    frozen Foundation contracts and can be replaced by a richer configuration
    service later without breaking existing commands.
    """

    root: Path
    config_dir: str = ".ntpe"
    file_name: str = "config.json"
    version: str = "ntpe-1.0-beta-stage-06.6"
    defaults: Dict[str, Any] = field(default_factory=lambda: json.loads(json.dumps(DEFAULT_CONFIG)))

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.directory = self.root / self.config_dir
        self.path = self.directory / self.file_name
        self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, replace: bool = False) -> Dict[str, Any]:
        if self.path.exists() and not replace:
            return self.load()
        data = self._wrap(self.defaults)
        self._write(data)
        return data

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self.create(replace=True)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if "settings" not in data:
            data = self._wrap(data)
            self._write(data)
        return data

    def settings(self) -> Dict[str, Any]:
        return dict(self.load().get("settings") or {})

    def _wrap(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": self.version,
            "updated_at": time.time(),
            "settings": json.loads(json.dumps(settings, ensure_ascii=False)),
        }

    def _write(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["updated_at"] = time.time()
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def _resolve(self, settings: Dict[str, Any], key: str) -> Any:
        current: Any = settings
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                raise KeyError(key)
            current = current[part]
        return current

    def get(self, key: Optional[str] = None) -> Any:
        settings = self.settings()
        if not key:
            return settings
        return self._resolve(settings, key)

    def set(self, key: str, value: Any) -> Dict[str, Any]:
        data = self.load()
        settings = dict(data.get("settings") or {})
        target = settings
        parts = key.split(".")
        for part in parts[:-1]:
            child = target.get(part)
            if not isinstance(child, dict):
                child = {}
                target[part] = child
            target = child
        target[parts[-1]] = value
        data["settings"] = settings
        return self._write(data)

    def reset(self) -> Dict[str, Any]:
        return self.create(replace=True)

    def export(self, output: Path) -> Dict[str, Any]:
        data = self.load()
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"output": str(output), "config": data}

    def import_file(self, package: Path, replace: bool = False) -> Dict[str, Any]:
        package = Path(package)
        incoming = json.loads(package.read_text(encoding="utf-8"))
        if "settings" not in incoming:
            incoming = self._wrap(incoming)
        if self.path.exists() and not replace:
            current = self.load()
            merged = dict(current.get("settings") or {})
            merged.update(dict(incoming.get("settings") or {}))
            incoming = self._wrap(merged)
        self._write(incoming)
        return incoming

    def validate(self) -> Dict[str, Any]:
        data = self.load()
        settings = data.get("settings") or {}
        errors = []
        if not isinstance(settings, dict):
            errors.append("settings must be an object")
        if not settings.get("provider"):
            errors.append("provider is required")
        if not settings.get("quality"):
            errors.append("quality is required")
        for section in ("runtime", "session", "benchmark", "translation"):
            if section in settings and not isinstance(settings[section], dict):
                errors.append(f"{section} must be an object")
        return {"valid": not errors, "errors": errors, "config": data}

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "cli_config_store",
            "version": self.version,
            "config_path": str(self.path),
            "default_keys": sorted(DEFAULT_CONFIG),
        }


def parse_config_value(value: str) -> Any:
    lowered = str(value).strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


__all__ = ["CLIConfigStore", "DEFAULT_CONFIG", "parse_config_value"]
