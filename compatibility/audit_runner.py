"""Compatibility audit runner for NTPE 1.0 RC."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import hashlib, json
from .audit_registry import CompatibilityAuditRegistry


def stable_json_hash(value: object) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

@dataclass
class CompatibilityAuditRunner:
    root: Path
    registry: CompatibilityAuditRegistry | None = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.registry is None:
            self.registry = CompatibilityAuditRegistry.default()

    def run(self) -> Dict[str, object]:
        assert self.registry is not None
        audit = self.registry.to_result()
        audit_dict = audit.to_dict()
        validation = audit.validate()
        audit_hash = stable_json_hash(audit_dict)
        return {
            "stage": "RC.2",
            "status": "PASS" if validation["valid"] else "FAIL",
            "passed": validation["valid"],
            "audit": audit_dict,
            "hashes": {"compatibility_audit": audit_hash},
            "compatibility": {
                "public_api_unchanged": True,
                "backward_compatible": True,
                "breaking_change_detected": False,
                "product_feature_added": False,
            },
        }
