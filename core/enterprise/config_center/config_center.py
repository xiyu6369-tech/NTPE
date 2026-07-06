from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .audit import ConfigAuditRecord, build_audit_record
from .config_loader import ConfigLoader
from .config_registry import ConfigRegistry
from .config_validator import ConfigValidator


class EnterpriseConfigCenter:
    """Stage-18.2 unified enterprise configuration facade."""

    stage = "Stage-18.2"
    name = "Enterprise Configuration Center"

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.loader = ConfigLoader(self.root)
        self.registry = ConfigRegistry()
        self.validator = ConfigValidator()
        self.config: Dict[str, Any] = {}
        self.audit_record: ConfigAuditRecord | None = None

    def load(self, environment: str | None = None, source: str | Path | None = None) -> Dict[str, Any]:
        config = self.loader.load(environment=environment, source=source)
        self.validator.validate(config)
        self.config = config
        self.audit_record = build_audit_record(config, validated=True, source=str(source or "profile"))
        return dict(config)

    def reload(self) -> Dict[str, Any]:
        env = self.config.get("enterprise", {}).get("environment") if self.config else None
        return self.load(environment=env)

    def validate(self, config: Dict[str, Any] | None = None) -> bool:
        return self.validator.validate(config or self.config)

    def register_provider(self, name: str, values: Dict[str, Any]) -> None:
        self.registry.register(name, values)

    def merged_registry_config(self) -> Dict[str, Any]:
        return self.registry.merge()

    def export(self, target: str | Path | None = None) -> str:
        payload = json.dumps(self.config, ensure_ascii=False, indent=2, sort_keys=True)
        if target:
            path = Path(target)
            if not path.is_absolute():
                path = self.root / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        return payload

    def import_config(self, source: str | Path) -> Dict[str, Any]:
        return self.load(source=source)

    def audit(self) -> Dict[str, Any]:
        if self.audit_record is None:
            self.audit_record = build_audit_record(self.config, validated=bool(self.config), source="memory")
        return self.audit_record.to_dict()
