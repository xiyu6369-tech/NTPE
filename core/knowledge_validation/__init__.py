"""
Knowledge Validation Engine - Offline Quality Gate
RM-5.7.3A Schema Validation Engine + RM-5.7.3B Business Rule Validation Engine

Provides JSON Schema validation and business rule validation for knowledge entities
without runtime dependencies.
"""

from core.knowledge_validation.business_validator import BusinessRuleValidator, BusinessValidationSummary
from core.knowledge_validation.schema_validator import SchemaValidator
from core.knowledge_validation.validation_codes import BusinessRuleCode
from core.knowledge_validation.validation_result import ValidationResult
from core.knowledge_validation.errors import (
    ValidationError,
    SchemaNotFoundError,
    SchemaVersionMismatchError,
    ValidationFailedError,
)

__all__ = [
    "SchemaValidator",
    "BusinessRuleValidator",
    "BusinessValidationSummary",
    "BusinessRuleCode",
    "ValidationResult",
    "ValidationError",
    "SchemaNotFoundError",
    "SchemaVersionMismatchError",
    "ValidationFailedError",
]

__version__ = "1.1.0"