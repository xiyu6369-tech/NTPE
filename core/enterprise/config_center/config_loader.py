from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .environment import EnvironmentManager
from .migration import ConfigMigration
from .profile_manager import ProfileManager


class ConfigLoader:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.environment = EnvironmentManager()
        self.profiles = ProfileManager()
        self.migration = ConfigMigration()

    def load(self, environment: str | None = None, source: str | Path | None = None) -> Dict[str, Any]:
        env = self.environment.normalize(environment)
        if source:
            path = Path(source)
            if not path.is_absolute():
                path = self.root / path
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = self.profiles.for_environment(env)
        data.setdefault("enterprise", {})["environment"] = env
        return self.migration.migrate(data)

    def save(self, config: Dict[str, Any], target: str | Path) -> Path:
        path = Path(target)
        if not path.is_absolute():
            path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
