"""
Base Models for Knowledge Extraction SDK (RM-5.7.2)

Defines the core data structures used across all knowledge extraction domains:
- KnowledgeEntity: Base entity for all extracted knowledge
- ExtractionResult: Result of an extraction operation
- ValidationResult: Result of validation operations
- CompilationResult: Result of compilation to runtime format
- ExtractionContext: Context passed during extraction
- EntityType: Enumeration of knowledge entity types
- ValidationSeverity: Enumeration of validation severity levels
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


def utc_now_iso() -> str:
    """Return a stable UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class EntityType(str, Enum):
    """Enumeration of knowledge entity types."""
    CHARACTER = "character"
    GLOSSARY = "glossary"
    SCENE = "scene"
    NARRATIVE = "narrative"
    STYLE = "style"
    UNKNOWN = "unknown"


class ValidationSeverity(str, Enum):
    """Enumeration of validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class KnowledgeEntity:
    """
    Base class for all extracted knowledge entities.
    
    Represents a single normalized knowledge entry that has been
    extracted, validated, and normalized from source text.
    """
    entity_id: str = field(default_factory=lambda: str(uuid4()))
    entity_type: EntityType = EntityType.UNKNOWN
    name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    source_text: str = ""
    source_location: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    version: int = 1
    
    # Relationships
    references: Dict[str, List[str]] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "attributes": dict(self.attributes),
            "source_text": self.source_text,
            "source_location": self.source_location,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "references": {k: list(v) for k, v in self.references.items()},
            "tags": list(self.tags),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntity":
        """Create entity from dictionary."""
        entity = cls(
            entity_id=data.get("entity_id", str(uuid4())),
            entity_type=EntityType(data.get("entity_type", "unknown")),
            name=data.get("name", ""),
            attributes=dict(data.get("attributes", {})),
            source_text=data.get("source_text", ""),
            source_location=data.get("source_location"),
            confidence=float(data.get("confidence", 0.0)),
            metadata=dict(data.get("metadata", {})),
            created_at=data.get("created_at", utc_now_iso()),
            updated_at=data.get("updated_at", utc_now_iso()),
            version=int(data.get("version", 1)),
            references={k: set(v) for k, v in data.get("references", {}).items()},
            tags=set(data.get("tags", [])),
        )
        return entity
    
    def add_reference(self, ref_type: str, target_id: str) -> None:
        """Add a reference to another entity."""
        if ref_type not in self.references:
            self.references[ref_type] = []
        if target_id not in self.references[ref_type]:
            self.references[ref_type].append(target_id)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = utc_now_iso()
        self.version += 1


@dataclass
class ExtractionContext:
    """
    Context passed to extractors during extraction.
    
    Contains document metadata, chunk information, and any
    domain-specific context needed for extraction.
    """
    document_id: str = ""
    document_title: str = ""
    chunk_id: str = ""
    chunk_index: int = 0
    chunk_text: str = ""
    chunk_start: int = 0
    chunk_end: int = 0
    domain_context: Dict[str, Any] = field(default_factory=dict)
    previous_entities: List[KnowledgeEntity] = field(default_factory=list)
    global_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "chunk_start": self.chunk_start,
            "chunk_end": self.chunk_end,
            "domain_context": dict(self.domain_context),
            "previous_entities": [e.to_dict() for e in self.previous_entities],
            "global_metadata": dict(self.global_metadata),
        }
@dataclass
class ExtractionResult:
    """
    Result of an extraction operation.
    
    Contains the extracted entities along with metadata about
    the extraction process.
    """
    success: bool
    entities: List[KnowledgeEntity] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extraction_time_ms: float = 0.0
    chunks_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_count(self) -> int:
        return len(self.entities)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "entities": [e.to_dict() for e in self.entities],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "extraction_time_ms": self.extraction_time_ms,
            "chunks_processed": self.chunks_processed,
            "entity_count": self.entity_count,
            "metadata": dict(self.metadata),
        }
    
    @classmethod
    def success_result(cls, entities: List[KnowledgeEntity], **kwargs) -> "ExtractionResult":
        """Create a successful extraction result."""
        return cls(success=True, entities=entities, **kwargs)
    
    @classmethod
    def failure_result(cls, errors: List[str], **kwargs) -> "ExtractionResult":
        """Create a failed extraction result."""
@dataclass
class ValidationIssue:
    """Single validation issue found during validation."""
    rule_id: str
    severity: ValidationSeverity
    message: str
    entity_id: Optional[str] = None
    field_path: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "entity_id": self.entity_id,
            "field_path": self.field_path,
            "expected": self.expected,
            "actual": self.actual,
            "metadata": dict(self.metadata),
        }


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Contains all validation issues found, categorized by severity.
    """
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_entities: List[KnowledgeEntity] = field(default_factory=list)
    validation_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    @property
    def infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue and update validity."""
        self.issues.append(issue)
        if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "validated_entities": [e.to_dict() for e in self.validated_entities],
            "validation_time_ms": self.validation_time_ms,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": len(self.infos),
            "metadata": dict(self.metadata),
        }
    
    @classmethod
    def valid_result(cls, entities: List[KnowledgeEntity], **kwargs) -> "ValidationResult":
        """Create a valid validation result."""
        return cls(is_valid=True, validated_entities=entities, **kwargs)
    
    @classmethod
    def invalid_result(cls, issues: List[ValidationIssue], **kwargs) -> "ValidationResult":
        """Create an invalid validation result."""
        return cls(is_valid=False, issues=issues, **kwargs)
@dataclass
class CompilationResult:
    """
    Result of compiling validated entities to runtime format.
    
    Contains the compiled output ready for use by the translation runtime.
    """
    success: bool
    compiled_data: Dict[str, Any] = field(default_factory=dict)
    entity_count: int = 0
    compilation_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    manifest: Optional["KnowledgeManifest"] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "compiled_data": dict(self.compiled_data),
            "entity_count": self.entity_count,
            "compilation_time_ms": self.compilation_time_ms,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
            "manifest": self.manifest.to_dict() if self.manifest else None,
        }
    
    @classmethod
    def success_result(cls, compiled_data: Dict[str, Any], entity_count: int, **kwargs) -> "CompilationResult":
        """Create a successful compilation result."""
        return cls(success=True, compiled_data=compiled_data, entity_count=entity_count, **kwargs)
    
    @classmethod
    def failure_result(cls, errors: List[str], **kwargs) -> "CompilationResult":
        """Create a failed compilation result."""
        return cls(success=False, errors=errors, **kwargs)


# Forward reference for CompilationResult
from .manifest import KnowledgeManifest