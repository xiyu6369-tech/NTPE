from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class ConfigAuditRecord:
    stage: str
    environment: str
    profile: str
    config_version: str
    config_hash: str
    validated: bool
    source: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_config_hash(config: Dict[str, Any]) -> str:
    raw = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_audit_record(config: Dict[str, Any], validated: bool, source: str) -> ConfigAuditRecord:
    enterprise = config.get("enterprise", {}) if isinstance(config, dict) else {}
    return ConfigAuditRecord(
        stage="Stage-18.2",
        environment=str(enterprise.get("environment", "development")),
        profile=str(enterprise.get("profile", "default")),
        config_version=str(enterprise.get("config_version", "1.2")),
        config_hash=build_config_hash(config),
        validated=validated,
        source=source,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
