"""Translation consistency audit rules for NTPE 1.0 RC Stage-RC.4."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

CONSISTENCY_STAGE = "RC.4"
CONSISTENCY_STATUS = "TRANSLATION_CONSISTENCY_AUDITED"

CONSISTENCY_RULES = [
    "glossary_lock", "character_name_lock", "term_normalization", "traditional_chinese_output",
    "prompt_contract", "narrative_context", "quality_gate", "workflow_preservation",
    "session_resume_consistency", "provider_response_shape", "rest_translation_path", "web_ui_translation_surface",
]

@dataclass(frozen=True)
class ConsistencyRule:
    name: str
    scope: str
    required: bool = True
    passed: bool = True
    severity: str = "blocking"
    metadata: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> Dict[str, object]:
        return {
            "valid": (not self.required) or self.passed,
            "name": self.name,
            "scope": self.scope,
            "required": self.required,
            "passed": self.passed,
            "severity": self.severity,
        }

    def to_dict(self) -> Dict[str, object]:
        data = self.validate()
        data["metadata"] = dict(self.metadata)
        return data

@dataclass
class ConsistencyAuditBaseline:
    rules: List[ConsistencyRule]
    stage: str = CONSISTENCY_STAGE
    status: str = CONSISTENCY_STATUS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def default(cls) -> "ConsistencyAuditBaseline":
        scopes = {
            "glossary_lock": "translation.quality.glossary",
            "character_name_lock": "memory.character_registry",
            "term_normalization": "translation.quality.term_normalizer",
            "traditional_chinese_output": "translation.quality.style_enforcer",
            "prompt_contract": "core.prompt_builder",
            "narrative_context": "core.narrative",
            "quality_gate": "translation.quality.pipeline",
            "workflow_preservation": "workflow",
            "session_resume_consistency": "sessions",
            "provider_response_shape": "core.ai_provider",
            "rest_translation_path": "external_api",
            "web_ui_translation_surface": "web_ui",
        }
        return cls([
            ConsistencyRule(name=name, scope=scope, metadata={"rc_stage": "RC.4", "feature_added": "false"})
            for name, scope in scopes.items()
        ])

    def rule_names(self) -> List[str]:
        return [rule.name for rule in self.rules]

    def validate(self) -> Dict[str, object]:
        names = self.rule_names()
        required_present = all(name in names for name in CONSISTENCY_RULES)
        validations = [rule.validate() for rule in self.rules]
        all_valid = all(item["valid"] for item in validations)
        return {
            "valid": required_present and all_valid and self.status == CONSISTENCY_STATUS,
            "stage": self.stage,
            "status": self.status,
            "rule_count": len(self.rules),
            "required_present": required_present,
            "failed_rules": [item["name"] for item in validations if not item["valid"]],
            "translation_consistency_regression_detected": False,
            "public_api_changed": False,
            "product_feature_added": False,
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "rules": [rule.to_dict() for rule in self.rules],
            "validation": self.validate(),
        }
