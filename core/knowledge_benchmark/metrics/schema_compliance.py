"""
Schema Compliance Metrics (RM-5.8.2)

Metrics for evaluating schema compliance, business rule compliance,
and review compliance per RM-5.8.0 METRICS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable

from ..models import (
    MetricName,
    MetricScore,
    EntityType,
    DifficultyTier,
    ExtractionComparison,
)


@dataclass
class SchemaField:
    """Schema field definition."""
    name: str
    field_type: str
    required: bool = False
    default: Any = None
    enum_values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class EntitySchema:
    """Entity schema definition."""
    entity_type: EntityType
    fields: Dict[str, SchemaField]
    version: str = "1.0"
ENTITY_SCHEMAS = {
    EntityType.CHARACTER: EntitySchema(
        entity_type=EntityType.CHARACTER,
        fields={
            "id": SchemaField("id", "string", required=True),
            "type": SchemaField("type", "string", required=True, enum_values=["character"]),
            "name": SchemaField("name", "string", required=True, min_length=1, max_length=100),
            "aliases": SchemaField("aliases", "list", required=False, default=[]),
            "attributes": SchemaField("attributes", "dict", required=False, default={}),
            "relationships": SchemaField("relationships", "list", required=False, default=[]),
            "appearances": SchemaField("appearances", "list", required=False, default=[]),
        },
        version="1.0",
    ),
    EntityType.GLOSSARY: EntitySchema(
        entity_type=EntityType.GLOSSARY,
        fields={
            "id": SchemaField("id", "string", required=True),
            "type": SchemaField("type", "string", required=True, enum_values=["glossary"]),
            "term": SchemaField("term", "string", required=True, min_length=1, max_length=200),
            "definition": SchemaField("definition", "string", required=True, max_length=2000),
            "translation": SchemaField("translation", "string", required=True, max_length=200),
            "context": SchemaField("context", "string", required=False, max_length=1000),
            "category": SchemaField("category", "string", required=False, max_length=50),
            "variants": SchemaField("variants", "list", required=False, default=[]),
        },
        version="1.0",
    ),
    EntityType.SCENE: EntitySchema(
        entity_type=EntityType.SCENE,
        fields={
            "id": SchemaField("id", "string", required=True),
            "type": SchemaField("type", "string", required=True, enum_values=["scene"]),
            "location": SchemaField("location", "string", required=True, max_length=200),
            "atmosphere": SchemaField("atmosphere", "string", required=False, max_length=1000),
            "sensory_details": SchemaField("sensory_details", "dict", required=False, default={}),
            "time_of_day": SchemaField("time_of_day", "string", required=False, max_length=50),
            "significance": SchemaField("significance", "string", required=False, max_length=1000),
        },
        version="1.0",
    ),
    EntityType.NARRATIVE: EntitySchema(
        entity_type=EntityType.NARRATIVE,
        fields={
            "id": SchemaField("id", "string", required=True),
            "type": SchemaField("type", "string", required=True, enum_values=["narrative"]),
            "plot_point": SchemaField("plot_point", "string", required=True, max_length=500),
            "arc": SchemaField("arc", "string", required=False, max_length=200),
            "tension_level": SchemaField("tension_level", "float", required=False, min_value=0.0, max_value=1.0),
            "pacing": SchemaField("pacing", "string", required=False, max_length=50),
            "foreshadowing": SchemaField("foreshadowing", "list", required=False, default=[]),
        },
        version="1.0",
    ),
    EntityType.STYLE: EntitySchema(
        entity_type=EntityType.STYLE,
        fields={
            "id": SchemaField("id", "string", required=True),
            "type": SchemaField("type", "string", required=True, enum_values=["style"]),
            "tone": SchemaField("tone", "string", required=True, max_length=100),
            "literary_devices": SchemaField("literary_devices", "list", required=False, default=[]),
            "sentence_patterns": SchemaField("sentence_patterns", "list", required=False, default=[]),
            "vocabulary_level": SchemaField("vocabulary_level", "string", required=False, max_length=50),
            "rhythm": SchemaField("rhythm", "string", required=False, max_length=100),
        },
        version="1.0",
    ),
}
class SchemaComplianceMetric:
    """Schema compliance metric.
    
    Schema_Pass_Rate = Valid_Entities / Total_Entities
    Target: 1.0 (100%) per RM-5.8.0
    """
    
    def __init__(self, schemas: Optional[Dict[EntityType, EntitySchema]] = None):
        self.schemas = schemas or ENTITY_SCHEMAS
    
    def validate_entity(self, entity: Dict[str, Any], schema: EntitySchema) -> List[str]:
        """Validate a single entity against schema."""
        errors = []
        
        for field_name, field_def in schema.fields.items():
            value = entity.get(field_name)
            
            if field_def.required and (value is None or value == ""):
                errors.append(f"Required field '{field_name}' is missing or empty")
                continue
            
            if value is None:
                continue
            
            if field_def.field_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be string")
            elif field_def.field_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be integer")
            elif field_def.field_type == "float" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be float")
            elif field_def.field_type == "list" and not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be list")
            elif field_def.field_type == "dict" and not isinstance(value, dict):
                errors.append(f"Field '{field_name}' must be dict")
            
            if field_def.enum_values is not None and value not in field_def.enum_values:
                errors.append(f"Field '{field_name}' value '{value}' not in allowed values: {field_def.enum_values}")
            
            if field_def.min_value is not None and isinstance(value, (int, float)) and value < field_def.min_value:
                errors.append(f"Field '{field_name}' value {value} below minimum {field_def.min_value}")
            if field_def.max_value is not None and isinstance(value, (int, float)) and value > field_def.max_value:
                errors.append(f"Field '{field_name}' value {value} above maximum {field_def.max_value}")
            
            if field_def.field_type == "string" and isinstance(value, str):
                if field_def.min_length is not None and len(value) < field_def.min_length:
                    errors.append(f"Field '{field_name}' length {len(value)} below minimum {field_def.min_length}")
                if field_def.max_length is not None and len(value) > field_def.max_length:
                    errors.append(f"Field '{field_name}' length {len(value)} above maximum {field_def.max_length}")
            
            if field_def.pattern and isinstance(value, str):
                import re
                if not re.match(field_def.pattern, value):
                    errors.append(f"Field '{field_name}' does not match pattern '{field_def.pattern}'")
        
        return errors
    
    def compute(
        self,
        comparison: ExtractionComparison,
    ) -> MetricScore:
        """Compute schema pass rate."""
        schema = self.schemas.get(comparison.extractor_type)
        if not schema:
            return MetricScore(
                metric_name=MetricName.SCHEMA_PASS_RATE,
                value=1.0,
                target=1.0,
                passed=True,
                details={"warning": f"No schema defined for {comparison.extractor_type.value}"},
                difficulty_tier=comparison.difficulty_tier,
            )
        
        total = len(comparison.predicted_entities)
        if total == 0:
            return MetricScore(
                metric_name=MetricName.SCHEMA_PASS_RATE,
                value=1.0,
                target=1.0,
                passed=True,
                details={"total_entities": 0, "valid_entities": 0},
                difficulty_tier=comparison.difficulty_tier,
            )
        
        valid_count = 0
        entity_results = []
        
        for entity in comparison.predicted_entities:
            errors = self.validate_entity(entity, schema)
            is_valid = len(errors) == 0
            if is_valid:
                valid_count += 1
            entity_results.append({
                "entity_id": entity.get("id", entity.get("entity_id", "")),
                "valid": is_valid,
                "errors": errors,
            })
        
        pass_rate = valid_count / total
        
        return MetricScore(
            metric_name=MetricName.SCHEMA_PASS_RATE,
            value=round(pass_rate, 4),
            target=1.0,
            passed=pass_rate >= 1.0,
            details={
                "total_entities": total,
                "valid_entities": valid_count,
                "invalid_entities": total - valid_count,
                "entity_results": entity_results,
            },
            difficulty_tier=comparison.difficulty_tier,
        )
BUSINESS_RULES: Dict[EntityType, List[Callable[[Dict[str, Any]], List[str]]]] = {
    EntityType.CHARACTER: [
        lambda e: [] if e.get("name") else ["Character must have a name"],
        lambda e: [] if e.get("id") else ["Character must have an ID"],
    ],
    EntityType.GLOSSARY: [
        lambda e: [] if e.get("term") else ["Glossary must have a term"],
        lambda e: [] if e.get("definition") else ["Glossary must have a definition"],
        lambda e: [] if e.get("translation") else ["Glossary must have a translation"],
    ],
    EntityType.SCENE: [
        lambda e: [] if e.get("location") else ["Scene must have a location"],
    ],
    EntityType.NARRATIVE: [
        lambda e: [] if e.get("plot_point") else ["Narrative must have a plot point"],
    ],
    EntityType.STYLE: [
        lambda e: [] if e.get("tone") else ["Style must have a tone"],
    ],
}


class BusinessRuleComplianceMetric:
    """Business rule compliance metric.
    
    Business_Rule_Pass_Rate = Rule_Compliant_Entities / Total_Entities
    Target: ≥ 0.95 per RM-5.8.0
    """
    
    def __init__(self, rules: Optional[Dict[EntityType, List[Callable]]] = None):
        self.rules = rules or BUSINESS_RULES
    
    def compute(
        self,
        comparison: ExtractionComparison,
    ) -> MetricScore:
        """Compute business rule pass rate."""
        rules = self.rules.get(comparison.extractor_type, [])
        
        total = len(comparison.predicted_entities)
        if total == 0:
            return MetricScore(
                metric_name=MetricName.BUSINESS_RULE_PASS_RATE,
                value=1.0,
                target=0.95,
                passed=True,
                details={"total_entities": 0, "compliant_entities": 0},
                difficulty_tier=comparison.difficulty_tier,
            )
        
        compliant_count = 0
        entity_results = []
        
        for entity in comparison.predicted_entities:
            all_errors = []
            for rule in rules:
                errors = rule(entity)
                all_errors.extend(errors)
            
            is_compliant = len(all_errors) == 0
            if is_compliant:
                compliant_count += 1
            entity_results.append({
                "entity_id": entity.get("id", entity.get("entity_id", "")),
                "compliant": is_compliant,
                "errors": all_errors,
            })
        
        pass_rate = compliant_count / total
        
        return MetricScore(
            metric_name=MetricName.BUSINESS_RULE_PASS_RATE,
            value=round(pass_rate, 4),
            target=0.95,
            passed=pass_rate >= 0.95,
            details={
                "total_entities": total,
                "compliant_entities": compliant_count,
                "non_compliant_entities": total - compliant_count,
                "entity_results": entity_results,
            },
            difficulty_tier=comparison.difficulty_tier,
        )
REVIEW_RULES: Dict[EntityType, List[Callable[[Dict[str, Any]], List[str]]]] = {
    EntityType.CHARACTER: [
        lambda e: [] if e.get("confidence", 0) >= 0.5 else ["Character confidence below 0.5"],
        lambda e: [] if e.get("name") and len(e.get("name", "")) > 1 else ["Character name too short"],
    ],
    EntityType.GLOSSARY: [
        lambda e: [] if e.get("confidence", 0) >= 0.5 else ["Glossary confidence below 0.5"],
        lambda e: [] if e.get("term") and e.get("translation") else ["Glossary missing term or translation"],
    ],
    EntityType.SCENE: [
        lambda e: [] if e.get("confidence", 0) >= 0.5 else ["Scene confidence below 0.5"],
    ],
    EntityType.NARRATIVE: [
        lambda e: [] if e.get("confidence", 0) >= 0.5 else ["Narrative confidence below 0.5"],
    ],
    EntityType.STYLE: [
        lambda e: [] if e.get("confidence", 0) >= 0.5 else ["Style confidence below 0.5"],
    ],
}


class ReviewComplianceMetric:
    """Review compliance metric (auto-review simulation).
    
    Review_Pass_Rate = Review_Approved_Entities / Total_Entities
    Target: ≥ 0.90 per RM-5.8.0
    """
    
    def __init__(self, rules: Optional[Dict[EntityType, List[Callable]]] = None):
        self.rules = rules or REVIEW_RULES
    
    def compute(
        self,
        comparison: ExtractionComparison,
    ) -> MetricScore:
        """Compute review pass rate."""
        rules = self.rules.get(comparison.extractor_type, [])
        
        total = len(comparison.predicted_entities)
        if total == 0:
            return MetricScore(
                metric_name=MetricName.REVIEW_PASS_RATE,
                value=1.0,
                target=0.90,
                passed=True,
                details={"total_entities": 0, "approved_entities": 0},
                difficulty_tier=comparison.difficulty_tier,
            )
        
        approved_count = 0
        entity_results = []
        
        for entity in comparison.predicted_entities:
            all_errors = []
            for rule in rules:
                errors = rule(entity)
                all_errors.extend(errors)
            
            is_approved = len(all_errors) == 0
            if is_approved:
                approved_count += 1
            entity_results.append({
                "entity_id": entity.get("id", entity.get("entity_id", "")),
                "approved": is_approved,
                "errors": all_errors,
            })
        
        pass_rate = approved_count / total
        
        return MetricScore(
            metric_name=MetricName.REVIEW_PASS_RATE,
            value=round(pass_rate, 4),
            target=0.90,
            passed=pass_rate >= 0.90,
            details={
                "total_entities": total,
                "approved_entities": approved_count,
                "rejected_entities": total - approved_count,
                "entity_results": entity_results,
            },
            difficulty_tier=comparison.difficulty_tier,
        )