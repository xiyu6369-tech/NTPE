from __future__ import annotations

from typing import Any, Dict, List

from .config_schema import EnterpriseConfigSchema


class ConfigValidationError(ValueError):
    """Raised when enterprise configuration fails validation."""


class ConfigValidator:
    def __init__(self, schema: EnterpriseConfigSchema | None = None) -> None:
        self.schema = schema or EnterpriseConfigSchema()

    def validate(self, config: Dict[str, Any]) -> bool:
        errors = self.collect_errors(config)
        if errors:
            raise ConfigValidationError("; ".join(errors))
        return True

    def collect_errors(self, config: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not isinstance(config, dict):
            return ["config must be a dictionary"]
        for section in self.schema.required_sections:
            if section not in config:
                errors.append(f"missing required section: {section}")
        enterprise = config.get("enterprise", {})
        if not isinstance(enterprise, dict):
            errors.append("enterprise section must be a dictionary")
            return errors
        for key in self.schema.enterprise_required_keys:
            if key not in enterprise:
                errors.append(f"missing enterprise key: {key}")
        return errors
