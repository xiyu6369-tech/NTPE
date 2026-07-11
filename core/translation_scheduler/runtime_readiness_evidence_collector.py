from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeReadinessEvidenceCollector:
    """Normalize caller-supplied readiness metadata without external reads."""

    stage = "3.7.3"
    sections = ("freezes", "checks", "versions", "reports")
    forbidden_raw_keys = frozenset({"source_text", "text", "chunks"})

    def collect(self, inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
        supplied = dict(inputs) if isinstance(inputs, Mapping) else {}
        collected: dict[str, dict[str, Any]] = {}
        missing_sections: list[str] = []

        for section in self.sections:
            value = supplied.get(section)
            if not isinstance(value, Mapping) or not value:
                collected[section] = {}
                missing_sections.append(section)
                continue
            collected[section] = self._sanitize_mapping(value)

        return {
            "collected_freezes": collected["freezes"],
            "collected_checks": collected["checks"],
            "collected_versions": collected["versions"],
            "collected_reports": collected["reports"],
            "missing_sections": missing_sections,
            "stage": self.stage,
            "metadata": {
                "collector": "runtime_readiness_evidence_collector",
                "stage": self.stage,
                "source": "supplied_mapping",
                "external_reads": False,
                "runtime_touch_mode": "none",
                "provider_touch_mode": "none",
                "launcher_touch_mode": "none",
                "real_runtime_allowed": False,
            },
        }

    def summarize(self, evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(evidence) if isinstance(evidence, Mapping) else {}
        missing = data.get("missing_sections")
        missing_sections = list(missing) if self._is_sequence(missing) else list(self.sections)
        return {
            "freezes_count": len(self._mapping(data.get("collected_freezes"))),
            "checks_count": len(self._mapping(data.get("collected_checks"))),
            "reports_count": len(self._mapping(data.get("collected_reports"))),
            "complete": not missing_sections,
            "missing_sections": missing_sections,
        }

    def validate_evidence(self, evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(evidence) if isinstance(evidence, Mapping) else {}
        errors: list[str] = []
        mapping_fields = (
            "collected_freezes",
            "collected_checks",
            "collected_versions",
            "collected_reports",
        )

        for key in mapping_fields:
            if not isinstance(data.get(key), Mapping):
                errors.append(f"{key} mapping is required")
        if not self._is_sequence(data.get("missing_sections")):
            errors.append("missing_sections list is required")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.7.3")
        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        forbidden_paths = self._find_forbidden_paths(data)
        for path in forbidden_paths:
            errors.append(f"forbidden raw field {path}")

        return {"valid": not errors, "errors": errors}

    def _sanitize_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in value.items():
            safe_key = str(key)
            if safe_key.lower() in self.forbidden_raw_keys:
                continue
            result[safe_key] = self._sanitize_value(item)
        return result

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return self._sanitize_mapping(value)
        if self._is_sequence(value):
            return [self._sanitize_value(item) for item in value]
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        return str(value)

    def _find_forbidden_paths(self, value: Any, path: str = "") -> list[str]:
        found: list[str] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = str(key)
                item_path = f"{path}.{key_text}" if path else key_text
                if key_text.lower() in self.forbidden_raw_keys:
                    found.append(item_path)
                found.extend(self._find_forbidden_paths(item, item_path))
        elif self._is_sequence(value):
            for index, item in enumerate(value):
                found.extend(self._find_forbidden_paths(item, f"{path}[{index}]"))
        return found

    @staticmethod
    def _mapping(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, Mapping) else {}

    @staticmethod
    def _is_sequence(value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


__all__ = ["RuntimeReadinessEvidenceCollector"]
