from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


class ConfigMigration:
    TARGET_VERSION = "1.2"

    def migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        migrated = deepcopy(config)
        enterprise = migrated.setdefault("enterprise", {})
        enterprise.setdefault("enabled", True)
        enterprise.setdefault("environment", "development")
        enterprise.setdefault("profile", "default")
        enterprise["config_version"] = self.TARGET_VERSION
        migrated.setdefault("runtime", {"mode": "compatible", "preserve_legacy": True})
        migrated.setdefault("translation", {"engine": "existing"})
        migrated.setdefault("platform", {"deployment": "local-workstation"})
        return migrated
