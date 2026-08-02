"""
Base Rule Class for Business Rule Validation
RM-5.7.3B Business Rule Validation Engine

Abstract base class for all business rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from core.knowledge_validation.validation_result import ValidationErrorDetail
from core.knowledge_validation.validation_codes import BusinessRuleCode


@dataclass(frozen=True)
class RuleContext:
    """Context passed to rule validation."""
    entity: dict
    entity_type: str
    all_entities: dict[str, list[dict]] | None = None  # For cross-entity rules (future use)


class BaseRule(ABC):
    """Abstract base class for business rules."""

    def __init__(self, rule_code: BusinessRuleCode, severity: str = "error"):
        self.rule_code = rule_code
        self.severity = severity

    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the domain this rule applies to (character, glossary, scene, narrative, style)."""
        pass

    @abstractmethod
    def validate(self, context: RuleContext) -> list[ValidationErrorDetail]:
        """Validate the entity against this rule.
        
        Returns:
            List of ValidationErrorDetail for each violation found.
            Empty list means validation passed.
        """
        pass

    def _create_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        instance_path: str = "",
    ) -> ValidationErrorDetail:
        """Create a ValidationErrorDetail for this rule."""
        return ValidationErrorDetail(
            keyword=self.rule_code.value,
            instance_path=instance_path or f"/{field}",
            schema_path=f"/business_rules/{self.domain}/{self.rule_code.value}",
            message=message,
            expected=None,
            actual=value,
        )


class EntityRule(BaseRule):
    """Base class for rules that validate a single entity."""

    def validate(self, context: RuleContext) -> list[ValidationErrorDetail]:
        """Validate a single entity."""
        return self._validate_entity(context.entity, context)

    @abstractmethod
    def _validate_entity(self, entity: dict, context: RuleContext) -> list[ValidationErrorDetail]:
        """Validate a single entity. To be implemented by subclasses."""
        pass


class DomainRule(BaseRule):
    """Base class for rules that validate across multiple entities in a domain."""

    def validate(self, context: RuleContext) -> list[ValidationErrorDetail]:
        """Validate across all entities in the domain."""
        if context.all_entities is None:
            return []
        domain_entities = context.all_entities.get(self.domain, [])
        return self._validate_domain(domain_entities, context)

    @abstractmethod
    def _validate_domain(self, entities: list[dict], context: RuleContext) -> list[ValidationErrorDetail]:
        """Validate across all entities in the domain. To be implemented by subclasses."""
        pass