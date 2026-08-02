"""
Error Definitions for Knowledge Extraction SDK (RM-5.7.2)

Defines all custom exceptions for the knowledge extraction pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class KnowledgeExtractionError(Exception):
    """Base exception for knowledge extraction errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class SchemaValidationError(KnowledgeExtractionError):
    """Raised when schema validation fails."""
    
    def __init__(self, message: str, field_path: str = "", expected: Any = None, actual: Any = None, errors: List[str] = None):
        details = {
            "field_path": field_path,
            "expected": expected,
            "actual": actual,
            "errors": errors or [],
        }
        super().__init__(message, details)
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        self.errors = errors or []


class BusinessRuleViolationError(KnowledgeExtractionError):
    """Raised when a business rule is violated."""
    
    def __init__(self, message: str, rule_id: str = "", entity_id: str = "", severity: str = "error"):
        details = {
            "rule_id": rule_id,
            "entity_id": entity_id,
            "severity": severity,
        }
        super().__init__(message, details)
        self.rule_id = rule_id
        self.entity_id = entity_id
        self.severity = severity


class ReferenceResolutionError(KnowledgeExtractionError):
    """Raised when a reference cannot be resolved."""
    
    def __init__(self, message: str, reference_type: str = "", reference_id: str = "", available_ids: List[str] = None):
        details = {
            "reference_type": reference_type,
            "reference_id": reference_id,
            "available_ids": available_ids or [],
        }
        super().__init__(message, details)
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.available_ids = available_ids or []


class ConfidenceThresholdError(KnowledgeExtractionError):
    """Raised when confidence is below required threshold."""
    
    def __init__(self, message: str, confidence: float = 0.0, threshold: float = 0.0, entity_id: str = ""):
        details = {
            "confidence": confidence,
            "threshold": threshold,
            "entity_id": entity_id,
        }
        super().__init__(message, details)
        self.confidence = confidence
        self.threshold = threshold
        self.entity_id = entity_id


class CompilationError(KnowledgeExtractionError):
    """Raised when compilation to runtime format fails."""
    
    def __init__(self, message: str, domain: str = "", entity_id: str = "", stage: str = ""):
        details = {
            "domain": domain,
            "entity_id": entity_id,
            "stage": stage,
        }
        super().__init__(message, details)
        self.domain = domain
        self.entity_id = entity_id
        self.stage = stage


class ManifestGenerationError(KnowledgeExtractionError):
    """Raised when manifest generation fails."""
    
    def __init__(self, message: str, manifest_path: str = "", reason: str = ""):
        details = {
            "manifest_path": manifest_path,
            "reason": reason,
        }
        super().__init__(message, details)
        self.manifest_path = manifest_path
        self.reason = reason


class ExtractionTimeoutError(KnowledgeExtractionError):
    """Raised when extraction times out."""
    
    def __init__(self, message: str, timeout_seconds: float = 0.0, chunk_id: str = ""):
        details = {
            "timeout_seconds": timeout_seconds,
            "chunk_id": chunk_id,
        }
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
        self.chunk_id = chunk_id


class NormalizationError(KnowledgeExtractionError):
    """Raised when entity normalization fails."""
    
    def __init__(self, message: str, entity_ids: List[str] = None, reason: str = ""):
        details = {
            "entity_ids": entity_ids or [],
            "reason": reason,
        }
        super().__init__(message, details)
        self.entity_ids = entity_ids or []
        self.reason = reason


class DuplicateEntityError(KnowledgeExtractionError):
    """Raised when duplicate entities are detected."""
    
    def __init__(self, message: str, duplicate_ids: List[str] = None, primary_id: str = ""):
        details = {
            "duplicate_ids": duplicate_ids or [],
            "primary_id": primary_id,
        }
        super().__init__(message, details)
        self.duplicate_ids = duplicate_ids or []
        self.primary_id = primary_id


class ConfigurationError(KnowledgeExtractionError):
    """Raised when extractor configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = "", expected: Any = None, actual: Any = None):
        details = {
            "config_key": config_key,
            "expected": expected,
            "actual": actual,
        }
        super().__init__(message, details)
        self.config_key = config_key
        self.expected = expected
        self.actual = actual
