"""
Validation Framework for Knowledge Extraction SDK (RM-5.7.2)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from .models import (
    KnowledgeEntity,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from .schema import KnowledgeSchema, SchemaValidator, DomainSchema


class ValidationPhase(str, Enum):
    SCHEMA = "schema"
    BUSINESS = "business"
    REFERENCE = "reference"
    CONFIDENCE = "confidence"
@dataclass
class ValidationRule:
    rule_id: str
    name: str
    description: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    validator: Callable = None
    phase: ValidationPhase = ValidationPhase.BUSINESS
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, entity, context):
        if self.validator:
            return self.validator(entity, context or {})
        return []


class BaseValidator(ABC):
    def __init__(self, name, phase):
        self.name = name
        self.phase = phase
        self.rules = []
    
    def add_rule(self, rule):
        self.rules.append(rule)
    
    @abstractmethod
    def validate(self, entities, context=None):
        pass
    
    def _create_issue(self, rule, entity, message, **kwargs):
        return ValidationIssue(
            rule_id=rule.rule_id,
            severity=rule.severity,
            message=message,
            entity_id=entity.entity_id,
            **kwargs
        )
class SchemaValidation(BaseValidator):
    def __init__(self, schema=None):
        super().__init__("schema_validation", ValidationPhase.SCHEMA)
        self.schema = schema
        self.validator = SchemaValidator(schema) if schema else None
    
    def set_schema(self, schema):
        self.schema = schema
        self.validator = SchemaValidator(schema)
    
    def validate(self, entities, context=None):
        issues = []
        if not self.validator:
            return issues
        for entity in entities:
            for error in self.validator.validate_entity(entity):
                issues.append(ValidationIssue(
                    rule_id="schema_validation",
                    severity=ValidationSeverity.ERROR,
                    message=error,
                    entity_id=entity.entity_id,
                    metadata={"schema_domain": self.schema.domain if self.schema else "unknown"}
                ))
        return issues


class BusinessValidation(BaseValidator):
    def __init__(self, domain="general"):
        super().__init__("business_validation", ValidationPhase.BUSINESS)
        self.domain = domain
        self._define_default_rules()
    
    def _define_default_rules(self):
        self.add_rule(ValidationRule(
            rule_id="entity_has_name",
            name="Entity Has Name",
            description="Entity must have a non-empty name",
            severity=ValidationSeverity.ERROR,
            validator=lambda e, c: ["Entity has no name"] if not e.name or not e.name.strip() else []
        ))
        self.add_rule(ValidationRule(
            rule_id="confidence_range",
            name="Confidence Range",
            description="Entity confidence must be between 0.0 and 1.0",
            severity=ValidationSeverity.ERROR,
            validator=lambda e, c: [f"Confidence {e.confidence} out of range [0.0, 1.0]"] if e.confidence < 0.0 or e.confidence > 1.0 else []
        ))
        self.add_rule(ValidationRule(
            rule_id="source_text_for_high_confidence",
            name="Source Text for High Confidence",
            description="High confidence entities should have source text",
            severity=ValidationSeverity.WARNING,
            validator=lambda e, c: ["High confidence entity missing source text"] if e.confidence > 0.8 and (not e.source_text or not e.source_text.strip()) else []
        ))
    
    def validate(self, entities, context=None):
        issues = []
        ctx = context or {}
        for entity in entities:
            for rule in self.rules:
                for error in rule.validate(entity, ctx):
                    issues.append(self._create_issue(rule, entity, error))
        return issues
class ReferenceValidation(BaseValidator):
    def __init__(self):
        super().__init__("reference_validation", ValidationPhase.REFERENCE)
        self._define_default_rules()
    
    def _define_default_rules(self):
        self.add_rule(ValidationRule(
            rule_id="valid_references",
            name="Valid References",
            description="All referenced entity IDs must exist",
            severity=ValidationSeverity.ERROR,
            validator=lambda e, c: [f"Reference to non-existent entity: {ref_id} (type: {ref_type})" for ref_type, ref_ids in e.references.items() for ref_id in ref_ids if ref_id not in c.get("entity_map", {})]
        ))
        self.add_rule(ValidationRule(
            rule_id="no_self_reference",
            name="No Self Reference",
            description="Entity cannot reference itself",
            severity=ValidationSeverity.WARNING,
            validator=lambda e, c: [f"Entity references itself in {ref_type}" for ref_type, ref_ids in e.references.items() if e.entity_id in ref_ids]
        ))
    
    def validate(self, entities, context=None):
        issues = []
        entity_map = {e.entity_id: e for e in entities}
        ctx = context or {}
        ctx["entity_map"] = entity_map
        for entity in entities:
            for rule in self.rules:
                for error in rule.validate(entity, ctx):
                    issues.append(self._create_issue(rule, entity, error))
        return issues


class ConfidenceValidation(BaseValidator):
    def __init__(self, min_confidence=0.0, max_confidence=1.0, warning_threshold=0.5, critical_threshold=0.3):
        super().__init__("confidence_validation", ValidationPhase.CONFIDENCE)
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._define_default_rules()
    
    def _define_default_rules(self):
        self.add_rule(ValidationRule(
            rule_id="confidence_bounds",
            name="Confidence Bounds",
            description=f"Confidence must be between {self.min_confidence} and {self.max_confidence}",
            severity=ValidationSeverity.ERROR,
            validator=lambda e, c: [f"Confidence {e.confidence} outside bounds [{self.min_confidence}, {self.max_confidence}]"] if e.confidence < self.min_confidence or e.confidence > self.max_confidence else []
        ))
        self.add_rule(ValidationRule(
            rule_id="low_confidence_warning",
            name="Low Confidence Warning",
            description=f"Confidence below {self.warning_threshold} may be unreliable",
            severity=ValidationSeverity.WARNING,
            validator=lambda e, c: [f"Low confidence: {e.confidence} (threshold: {self.warning_threshold})"] if e.confidence < self.warning_threshold else []
        ))
        self.add_rule(ValidationRule(
            rule_id="critical_confidence",
            name="Critical Confidence",
            description=f"Confidence below {self.critical_threshold} is critically low",
            severity=ValidationSeverity.CRITICAL,
            validator=lambda e, c: [f"Critically low confidence: {e.confidence} (threshold: {self.critical_threshold})"] if e.confidence < self.critical_threshold else []
        ))
    
    def validate(self, entities, context=None):
        issues = []
        for entity in entities:
            for rule in self.rules:
                for error in rule.validate(entity, context or {}):
                    issues.append(self._create_issue(rule, entity, error))
        return issues
class ValidationPipeline:
    PHASE_ORDER = [ValidationPhase.SCHEMA, ValidationPhase.BUSINESS, ValidationPhase.REFERENCE, ValidationPhase.CONFIDENCE]
    
    def __init__(self):
        self.validators = {phase: [] for phase in ValidationPhase}
    
    def add_validator(self, validator):
        self.validators[validator.phase].append(validator)
    
    def validate(self, entities, context=None):
        import time
        start_time = time.perf_counter()
        all_issues = []
        validated_entities = list(entities)
        ctx = context or {}
        for phase in self.PHASE_ORDER:
            for validator in self.validators[phase]:
                all_issues.extend(validator.validate(validated_entities, ctx))
        validation_time_ms = (time.perf_counter() - start_time) * 1000
        has_errors = any(i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) for i in all_issues)
        return ValidationResult(
            is_valid=not has_errors,
            issues=all_issues,
            validated_entities=validated_entities,
            validation_time_ms=validation_time_ms,
            metadata={"phases_run": len([p for p in self.PHASE_ORDER if self.validators[p]]), "total_validators": sum(len(v) for v in self.validators.values())}
        )
    
    @classmethod
    def create_default(cls, domain="general", schema=None):
        pipeline = cls()
        pipeline.add_validator(SchemaValidation(schema or DomainSchema.get(domain)))
        pipeline.add_validator(BusinessValidation(domain))
        pipeline.add_validator(ReferenceValidation())
        pipeline.add_validator(ConfidenceValidation())
        return pipeline


@dataclass
class ValidationContext:
    document_id: str = ""
    domain: str = ""
    entity_map: Dict[str, KnowledgeEntity] = field(default_factory=dict)
    previous_validations: List = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
