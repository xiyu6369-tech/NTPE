"""
Schema Definitions for Knowledge Extraction SDK (RM-5.7.2)

Defines the schema system for validating extracted knowledge entities.
Each domain (Character, Glossary, Scene, Narrative, Style) has its own
schema definition with required fields, types, and validation rules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
import re


class FieldType(str, Enum):
    """Supported field types in schemas."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ENTITY_REF = "entity_ref"
    ENUM = "enum"
    DATETIME = "datetime"
    CONFIDENCE = "confidence"


@dataclass
class SchemaField:
    """
    Definition of a single field in a knowledge schema.
    """
    name: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    description: str = ""
    validators: List[Callable[[Any], bool]] = field(default_factory=list)
    enum_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    def validate(self, value: Any) -> List[str]:
        """Validate a value against this field's constraints."""
        errors = []
        
        if self.required and value is None:
            errors.append(f"Field '{self.name}' is required")
            return errors
        
        if value is None:
            return errors
        
        type_errors = self._validate_type(value)
        errors.extend(type_errors)
        
        for validator in self.validators:
            try:
                if not validator(value):
                    errors.append(f"Field '{self.name}' failed custom validation")
            except Exception as e:
                errors.append(f"Field '{self.name}' validator error: {e}")
        
        if self.enum_values is not None and value not in self.enum_values:
            errors.append(f"Field '{self.name}' value '{value}' not in allowed values: {self.enum_values}")
        
        if self.field_type in (FieldType.INTEGER, FieldType.FLOAT, FieldType.CONFIDENCE):
            if self.min_value is not None and value < self.min_value:
                errors.append(f"Field '{self.name}' value {value} below minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                errors.append(f"Field '{self.name}' value {value} above maximum {self.max_value}")
        
        if self.field_type in (FieldType.STRING, FieldType.LIST):
            length = len(value) if hasattr(value, '__len__') else 0
            if self.min_length is not None and length < self.min_length:
                errors.append(f"Field '{self.name}' length {length} below minimum {self.min_length}")
            if self.max_length is not None and length > self.max_length:
                errors.append(f"Field '{self.name}' length {length} above maximum {self.max_length}")
        
        if self.field_type == FieldType.STRING and self.pattern:
            if not re.match(self.pattern, str(value)):
                errors.append(f"Field '{self.name}' value does not match pattern '{self.pattern}'")
        
        return errors
    
    def _validate_type(self, value: Any) -> List[str]:
        """Validate the type of a value."""
        errors = []
        
        type_checks = {
            FieldType.STRING: lambda v: isinstance(v, str),
            FieldType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            FieldType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            FieldType.BOOLEAN: lambda v: isinstance(v, bool),
            FieldType.LIST: lambda v: isinstance(v, list),
            FieldType.DICT: lambda v: isinstance(v, dict),
            FieldType.CONFIDENCE: lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
        }
        
        if self.field_type in type_checks:
            if not type_checks[self.field_type](value):
                errors.append(f"Field '{self.name}' expected type {self.field_type.value}, got {type(value).__name__}")
        
class KnowledgeSchema(ABC):
    """
    Abstract base class for knowledge domain schemas.
    
    Each domain (Character, Glossary, Scene, Narrative, Style)
    implements its own schema by defining fields and validation rules.
    """
    
    def __init__(self, domain: str, version: str = "1.0"):
        self.domain = domain
        self.version = version
        self._fields: Dict[str, SchemaField] = {}
        self._define_fields()
    
    @abstractmethod
    def _define_fields(self) -> None:
        """Define the schema fields. Implemented by subclasses."""
        pass
    
    def add_field(self, field: SchemaField) -> None:
        """Add a field to the schema."""
        self._fields[field.name] = field
    
    def get_field(self, name: str) -> Optional[SchemaField]:
        """Get a field by name."""
        return self._fields.get(name)
    
    def get_fields(self) -> Dict[str, SchemaField]:
        """Get all fields."""
        return dict(self._fields)
    
    def get_required_fields(self) -> List[str]:
        """Get names of required fields."""
        return [name for name, field in self._fields.items() if field.required]
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against this schema.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        for field_name in self.get_required_fields():
            if field_name not in data:
                errors.append(f"Required field '{field_name}' is missing")
        
        for field_name, value in data.items():
            field = self._fields.get(field_name)
            if field:
                field_errors = field.validate(value)
                errors.extend(field_errors)
        
        return errors
    
    def validate_entity(self, entity: "KnowledgeEntity") -> List[str]:
        """
        Validate a KnowledgeEntity against this schema.
        
        Returns:
            List of error messages (empty if valid)
        """
        from .models import KnowledgeEntity
        data = entity.attributes.copy()
        data["name"] = entity.name
        data["confidence"] = entity.confidence
        data["source_text"] = entity.source_text
        return self.validate(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize schema to dictionary."""
        return {
            "domain": self.domain,
            "version": self.version,
            "fields": {
                name: {
                    "name": field.name,
                    "type": field.field_type.value,
                    "required": field.required,
                    "default": field.default,
                    "description": field.description,
                    "enum_values": field.enum_values,
                    "min_value": field.min_value,
                    "max_value": field.max_value,
                    "pattern": field.pattern,
                    "min_length": field.min_length,
                    "max_length": field.max_length,
                }
                for name, field in self._fields.items()
            }
}


class SchemaValidator:
    """
    Validator that uses KnowledgeSchema to validate entities.
    
    Provides a unified interface for schema validation across domains.
    """
    
    def __init__(self, schema: KnowledgeSchema):
        self.schema = schema
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against the schema."""
        return self.schema.validate(data)
    
    def validate_entity(self, entity: "KnowledgeEntity") -> List[str]:
        """Validate entity against the schema."""
        return self.schema.validate_entity(entity)
    
    def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if data is valid."""
        return len(self.validate(data)) == 0
    
    def is_valid_entity(self, entity: "KnowledgeEntity") -> bool:
        """Check if entity is valid."""
        return len(self.validate_entity(entity)) == 0


# Domain-specific schemas

class CharacterSchema(KnowledgeSchema):
    """Schema for Character entities."""
    
    def _define_fields(self) -> None:
        self.add_field(SchemaField(
            name="name",
            field_type=FieldType.STRING,
            required=True,
            description="Character's primary name",
            min_length=1,
            max_length=100,
        ))
        self.add_field(SchemaField(
            name="aliases",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="Alternative names for the character",
        ))
        self.add_field(SchemaField(
            name="role",
            field_type=FieldType.STRING,
            required=False,
            description="Character's role in the story",
            max_length=50,
        ))
        self.add_field(SchemaField(
            name="gender",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["male", "female", "non-binary", "unknown", "other"],
            description="Character's gender",
        ))
        self.add_field(SchemaField(
            name="age",
            field_type=FieldType.STRING,
            required=False,
            description="Character's age or age range",
        ))
        self.add_field(SchemaField(
            name="description",
            field_type=FieldType.STRING,
            required=False,
            description="Physical and personality description",
            max_length=1000,
        ))
        self.add_field(SchemaField(
            name="relationships",
            field_type=FieldType.DICT,
            required=False,
            default={},
            description="Relationships to other characters",
        ))
        self.add_field(SchemaField(
            name="first_appearance",
            field_type=FieldType.STRING,
            required=False,
            description="Chapter/scene where character first appears",
        ))
        self.add_field(SchemaField(
            name="importance",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["protagonist", "major", "minor", "background"],
            default="minor",
            description="Character's importance level",
        ))
        self.add_field(SchemaField(
            name="confidence",
            field_type=FieldType.CONFIDENCE,
            required=True,
            default=0.5,
            description="Extraction confidence score",
        ))


class GlossarySchema(KnowledgeSchema):
    """Schema for Glossary/Term entities."""
    
    def _define_fields(self) -> None:
        self.add_field(SchemaField(
            name="term",
            field_type=FieldType.STRING,
            required=True,
            description="Source term in original language",
            min_length=1,
            max_length=200,
        ))
        self.add_field(SchemaField(
            name="translation",
            field_type=FieldType.STRING,
            required=True,
            description="Translated term in target language",
            min_length=1,
            max_length=200,
        ))
        self.add_field(SchemaField(
            name="category",
            field_type=FieldType.STRING,
            required=False,
            description="Term category (e.g., 'proper_noun', 'technical', 'cultural')",
            max_length=50,
        ))
        self.add_field(SchemaField(
            name="context",
            field_type=FieldType.STRING,
            required=False,
            description="Usage context or domain",
            max_length=500,
        ))
        self.add_field(SchemaField(
            name="part_of_speech",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["noun", "verb", "adjective", "adverb", "proper_noun", "phrase", "other"],
            description="Grammatical category",
        ))
        self.add_field(SchemaField(
            name="notes",
            field_type=FieldType.STRING,
            required=False,
            description="Additional notes or disambiguation",
            max_length=1000,
        ))
        self.add_field(SchemaField(
            name="locked",
            field_type=FieldType.BOOLEAN,
            required=False,
            default=False,
            description="Whether translation is locked/finalized",
        ))
        self.add_field(SchemaField(
            name="frequency",
            field_type=FieldType.INTEGER,
            required=False,
            default=0,
            min_value=0,
            description="Occurrence count in source text",
        ))
        self.add_field(SchemaField(
            name="confidence",
            field_type=FieldType.CONFIDENCE,
            required=True,
            default=0.5,
            description="Extraction confidence score",
        ))
class SceneSchema(KnowledgeSchema):
    """Schema for Scene entities."""
    
    def _define_fields(self) -> None:
        self.add_field(SchemaField(
            name="scene_id",
            field_type=FieldType.STRING,
            required=True,
            description="Unique scene identifier",
            min_length=1,
            max_length=50,
        ))
        self.add_field(SchemaField(
            name="title",
            field_type=FieldType.STRING,
            required=False,
            description="Scene title or summary",
            max_length=200,
        ))
        self.add_field(SchemaField(
            name="location",
            field_type=FieldType.STRING,
            required=False,
            description="Scene location/setting",
            max_length=200,
        ))
        self.add_field(SchemaField(
            name="time",
            field_type=FieldType.STRING,
            required=False,
            description="Time of day or temporal setting",
            max_length=100,
        ))
        self.add_field(SchemaField(
            name="characters_present",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="List of character entity IDs present in scene",
        ))
        self.add_field(SchemaField(
            name="atmosphere",
            field_type=FieldType.STRING,
            required=False,
            description="Scene atmosphere/mood",
            max_length=500,
        ))
        self.add_field(SchemaField(
            name="key_events",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="Key events occurring in this scene",
        ))
        self.add_field(SchemaField(
            name="chapter",
            field_type=FieldType.INTEGER,
            required=False,
            min_value=0,
            description="Chapter number",
        ))
        self.add_field(SchemaField(
            name="sequence",
            field_type=FieldType.INTEGER,
            required=False,
            min_value=0,
            description="Scene sequence within chapter",
        ))
        self.add_field(SchemaField(
            name="confidence",
            field_type=FieldType.CONFIDENCE,
            required=True,
            default=0.5,
            description="Extraction confidence score",
        ))


class NarrativeSchema(KnowledgeSchema):
    """Schema for Narrative entities."""
    
    def _define_fields(self) -> None:
        self.add_field(SchemaField(
            name="arc_id",
            field_type=FieldType.STRING,
            required=True,
            description="Narrative arc identifier",
            min_length=1,
            max_length=50,
        ))
        self.add_field(SchemaField(
            name="title",
            field_type=FieldType.STRING,
            required=True,
            description="Narrative arc title",
            min_length=1,
            max_length=200,
        ))
        self.add_field(SchemaField(
            name="type",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["main_plot", "subplot", "character_arc", "theme", "flashback", "foreshadowing"],
            default="subplot",
            description="Type of narrative element",
        ))
        self.add_field(SchemaField(
            name="description",
            field_type=FieldType.STRING,
            required=False,
            description="Detailed description of the narrative element",
            max_length=2000,
        ))
        self.add_field(SchemaField(
            name="involved_characters",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="Character entity IDs involved",
        ))
        self.add_field(SchemaField(
            name="start_chapter",
            field_type=FieldType.INTEGER,
            required=False,
            min_value=0,
            description="Starting chapter",
        ))
        self.add_field(SchemaField(
            name="end_chapter",
            field_type=FieldType.INTEGER,
            required=False,
            min_value=0,
            description="Ending chapter",
        ))
        self.add_field(SchemaField(
            name="status",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["setup", "development", "climax", "resolution", "abandoned"],
            default="development",
            description="Current status of narrative arc",
        ))
        self.add_field(SchemaField(
            name="themes",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="Associated themes",
        ))
        self.add_field(SchemaField(
            name="confidence",
            field_type=FieldType.CONFIDENCE,
            required=True,
            default=0.5,
            description="Extraction confidence score",
        ))
class StyleSchema(KnowledgeSchema):
    """Schema for Style entities."""
    
    def _define_fields(self) -> None:
        self.add_field(SchemaField(
            name="style_id",
            field_type=FieldType.STRING,
            required=True,
            description="Style identifier",
            min_length=1,
            max_length=50,
        ))
        self.add_field(SchemaField(
            name="name",
            field_type=FieldType.STRING,
            required=True,
            description="Style name",
            min_length=1,
            max_length=100,
        ))
        self.add_field(SchemaField(
            name="category",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["tone", "voice", "register", "diction", "syntax", "figurative", "pacing", "other"],
            description="Style category",
        ))
        self.add_field(SchemaField(
            name="description",
            field_type=FieldType.STRING,
            required=False,
            description="Detailed style description",
            max_length=1000,
        ))
        self.add_field(SchemaField(
            name="examples",
            field_type=FieldType.LIST,
            required=False,
            default=[],
            description="Example passages illustrating the style",
        ))
        self.add_field(SchemaField(
            name="rules",
            field_type=FieldType.DICT,
            required=False,
            default={},
            description="Specific style rules or guidelines",
        ))
        self.add_field(SchemaField(
            name="applies_to",
            field_type=FieldType.ENUM,
            required=False,
            enum_values=["global", "character", "scene", "narrative", "dialogue", "narration"],
            default="global",
            description="Scope of style application",
        ))
        self.add_field(SchemaField(
            name="priority",
            field_type=FieldType.INTEGER,
            required=False,
            default=50,
            min_value=0,
            max_value=100,
            description="Priority when multiple styles apply",
        ))
        self.add_field(SchemaField(
            name="confidence",
            field_type=FieldType.CONFIDENCE,
            required=True,
            default=0.5,
            description="Extraction confidence score",
        ))


# Pre-defined schema instances
CHARACTER_SCHEMA = CharacterSchema("character", "1.0")
GLOSSARY_SCHEMA = GlossarySchema("glossary", "1.0")
SCENE_SCHEMA = SceneSchema("scene", "1.0")
NARRATIVE_SCHEMA = NarrativeSchema("narrative", "1.0")
STYLE_SCHEMA = StyleSchema("style", "1.0")


# Domain schema registry
class DomainSchema:
    """Registry of domain schemas."""
    
    _schemas: Dict[str, KnowledgeSchema] = {
        "character": CHARACTER_SCHEMA,
        "glossary": GLOSSARY_SCHEMA,
        "scene": SCENE_SCHEMA,
        "narrative": NARRATIVE_SCHEMA,
        "style": STYLE_SCHEMA,
    }
    
    @classmethod
    def get(cls, domain: str) -> Optional[KnowledgeSchema]:
        """Get schema for a domain."""
        return cls._schemas.get(domain.lower())
    
    @classmethod
    def register(cls, domain: str, schema: KnowledgeSchema) -> None:
        """Register a custom schema."""
        cls._schemas[domain.lower()] = schema
    
    @classmethod
    def list_domains(cls) -> List[str]:
        """List all registered domains."""
        return list(cls._schemas.keys())
    
    @classmethod
    def get_validator(cls, domain: str) -> Optional[SchemaValidator]:
        """Get validator for a domain."""
        schema = cls.get(domain)
        if schema:
            return SchemaValidator(schema)
        return None
        return errors