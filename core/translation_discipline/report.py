from __future__ import annotations

from typing import Any
from .rule import DisciplineRule


def build_discipline_report(profile: str, rules: tuple[DisciplineRule, ...], *, legacy_mappings: dict[str, str] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    encoded = [rule.to_dict() for rule in rules]
    return {"schema_version": "6.0.0-stage01", "engine_version": "6.0.0", "profile": profile, "active_rules": encoded, "generation_rules": [item for item in encoded if item["phase"] == "generation"], "local_repair_rules": [item for item in encoded if item["phase"] == "local_repair"], "quality_rules": [item for item in encoded if item["phase"] == "quality_validation"], "adaptive_retry_rules": [item for item in encoded if item["phase"] == "adaptive_retry"], "legacy_mappings": dict(legacy_mappings or {}), "warnings": list(warnings or [])}
