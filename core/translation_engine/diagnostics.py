"""Translation diagnostics."""
from __future__ import annotations
from typing import Any, Dict, List


class TranslationDiagnostics:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def record(self, name: str, payload: Dict[str, Any] | None = None, severity: str = "info") -> Dict[str, Any]:
        item = {"name": name, "payload": dict(payload or {}), "severity": severity}
        self.records.append(item)
        return item

    def health_report(self) -> Dict[str, Any]:
        errors = [r for r in self.records if r.get("severity") == "error"]
        warnings = [r for r in self.records if r.get("severity") == "warning"]
        return {"type": "translation_health_report", "healthy": not errors, "errors": len(errors), "warnings": len(warnings), "records": list(self.records)}

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_diagnostics", "record_count": len(self.records), "healthy": self.health_report()["healthy"]}
