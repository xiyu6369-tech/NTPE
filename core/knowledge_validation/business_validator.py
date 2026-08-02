"""
Business Rule Validator
RM-5.7.3B Business Rule Validation Engine

Main validator class that orchestrates business rule validation across domains.
Reuses ValidationResult from RM-5.7.3A.
"""

from dataclasses import dataclass, field
from typing import Any

from core.knowledge_validation.rules.base import RuleContext
from core.knowledge_validation.rules.registry import (
    get_all_rules,
    get_rules_for_domain,
    list_domains,
)
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationErrorDetail, ValidationResult


@dataclass
class BusinessValidationSummary:
    """Summary of business rule validation across domains."""
    total_entities: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    domains_validated: list[str] = field(default_factory=list)
    errors_by_domain: dict[str, int] = field(default_factory=dict)
    errors_by_code: dict[str, int] = field(default_factory=dict)


class BusinessRuleValidator:
    """
    Business Rule Validator for Knowledge Generation pipeline.
    
    Validates domain-specific business rules after schema validation.
    No production runtime integration, no provider calls, no review workflow.
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the business rule validator.
        
        Args:
            strict_mode: If True, treat all violations as errors. If False, some may be warnings.
        """
        self.strict_mode = strict_mode

    def validate(self, entity: dict, domain: str | None = None) -> ValidationResult:
        """
        Validate a single entity against business rules.
        
        Args:
            entity: The entity dictionary to validate.
            domain: Optional domain hint (character, glossary, scene, narrative, style).
                   If not provided, inferred from entity_type.
        
        Returns:
            ValidationResult with business rule violations.
        """
        if domain is None:
            domain = self._infer_domain(entity)

        if domain is None:
            return ValidationResult.success(
                schema="business_rules",
                metadata={"skipped": True, "reason": "Could not infer domain"},
            )

        rules = get_rules_for_domain(domain)
        if not rules:
            return ValidationResult.success(
                schema=f"business_rules.{domain}",
                metadata={"skipped": True, "reason": f"No rules for domain: {domain}"},
            )

        context = RuleContext(entity=entity, entity_type=domain)
        all_errors = []

        for rule in rules:
            errors = rule.validate(context)
            all_errors.extend(errors)

        schema_name = f"business_rules.{domain}"
        if all_errors:
            return ValidationResult.failure(
                schema=schema_name,
                errors=all_errors,
            )

        return ValidationResult.success(schema=schema_name)
    def validate_many(self, entities: list[dict], domain: str | None = None) -> list[ValidationResult]:
        """
        Validate multiple entities of the same domain.
        
        Args:
            entities: List of entity dictionaries.
            domain: Domain for all entities (required for cross-entity rules).
        
        Returns:
            List of ValidationResult, one per entity.
        """
        if domain is None and entities:
            domain = self._infer_domain(entities[0])

        if domain is None:
            return [
                ValidationResult.success(
                    schema="business_rules",
                    metadata={"skipped": True, "reason": "Could not infer domain"},
                )
                for _ in entities
            ]

        rules = get_rules_for_domain(domain)
        domain_rules = [r for r in rules if hasattr(r, '_validate_domain')]
        entity_rules = [r for r in rules if not hasattr(r, '_validate_domain')]

        results = []
        for i, entity in enumerate(entities):
            context = RuleContext(entity=entity, entity_type=domain, all_entities={domain: entities})
            all_errors = []

            for rule in entity_rules:
                errors = rule.validate(context)
                all_errors.extend(errors)

            for rule in domain_rules:
                errors = rule.validate(context)
                all_errors.extend(errors)

            schema_name = f"business_rules.{domain}"
            if all_errors:
                results.append(ValidationResult.failure(schema=schema_name, errors=all_errors))
            else:
                results.append(ValidationResult.success(schema=schema_name))

        return results

    def validate_domain(self, domain: str, entities: list[dict]) -> ValidationResult:
        """
        Validate all entities in a domain, including cross-entity rules.
        
        Args:
            domain: Domain name (character, glossary, scene, narrative, style).
            entities: List of entities in that domain.
        
        Returns:
            Aggregated ValidationResult for the domain.
        """
        rules = get_rules_for_domain(domain)
        if not rules:
            return ValidationResult.success(
                schema=f"business_rules.{domain}",
                metadata={"skipped": True, "reason": f"No rules for domain: {domain}"},
            )

        all_entities = {domain: entities}
        all_errors = []

        for entity in entities:
            context = RuleContext(entity=entity, entity_type=domain, all_entities=all_entities)
            for rule in rules:
                if not hasattr(rule, '_validate_domain'):
                    errors = rule.validate(context)
                    all_errors.extend(errors)

        for rule in rules:
            if hasattr(rule, '_validate_domain'):
                context = RuleContext(entity={}, entity_type=domain, all_entities=all_entities)
                errors = rule.validate(context)
                all_errors.extend(errors)

        schema_name = f"business_rules.{domain}"
        if all_errors:
            return ValidationResult.failure(
                schema=schema_name,
                errors=all_errors,
            )

        return ValidationResult.success(schema=schema_name)

    def validate_all_domains(self, entities_by_domain: dict[str, list[dict]]) -> dict[str, ValidationResult]:
        """
        Validate entities across all domains.
        
        Args:
            entities_by_domain: Dict mapping domain name to list of entities.
        
        Returns:
            Dict mapping domain to ValidationResult.
        """
        results = {}
        for domain, entities in entities_by_domain.items():
            if domain in list_domains():
                results[domain] = self.validate_domain(domain, entities)
            else:
                results[domain] = ValidationResult.success(
                    schema=f"business_rules.{domain}",
                    metadata={"skipped": True, "reason": f"Unknown domain: {domain}"},
                )
        return results

    def get_summary(self, results: dict[str, ValidationResult]) -> BusinessValidationSummary:
        """Generate a summary from validation results."""
        summary = BusinessValidationSummary()

        for domain, result in results.items():
            if result.metadata.get("skipped"):
                continue

            summary.domains_validated.append(domain)
            error_count = result.error_count
            summary.total_errors += error_count
            summary.errors_by_domain[domain] = error_count

            for error in result.errors:
                summary.errors_by_code[error.keyword] = summary.errors_by_code.get(error.keyword, 0) + 1

        return summary

    def _infer_domain(self, entity: dict) -> str | None:
        """Infer domain from entity_type field."""
        entity_type = entity.get("entity_type")
        if entity_type:
            type_map = {
                "character": "character",
                "glossary": "glossary",
                "scene": "scene",
                "narrative": "narrative",
                "style": "style",
            }
            return type_map.get(entity_type.lower())
        return None