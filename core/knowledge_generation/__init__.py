"""
Knowledge Generation SDK (RM-5.7.2)

This module provides the foundational SDK for knowledge extraction in NTPE.
It defines base models, extractor interfaces, validation framework,
compiler interface, and manifest system for all knowledge domains.

Domains: Character, Glossary, Scene, Narrative, Style

Architecture:
    Document -> Chunk -> Extractor -> Validation -> Normalized Entity -> Review -> Compiler -> Runtime Knowledge

The five domain extractors (Character, Glossary, Scene, Narrative, Style)
share 90% common infrastructure. Only Prompt and Schema differ.
"""

from __future__ import annotations

# Base Models
from .models import (
    KnowledgeEntity,
    ExtractionResult,
    ValidationResult,
    CompilationResult,
    ExtractionContext,
    EntityType,
    ValidationSeverity,
)

# Schema
from .schema import (
    KnowledgeSchema,
    SchemaField,
    SchemaValidator,
    DomainSchema,
    CHARACTER_SCHEMA,
    GLOSSARY_SCHEMA,
    SCENE_SCHEMA,
    NARRATIVE_SCHEMA,
    STYLE_SCHEMA,
)

# Extractor Base
from .extractor_base import (
    BaseKnowledgeExtractor,
    ExtractionStrategy,
    ExtractorConfig,
)

# Validation Framework
from .validator import (
    ValidationRule,
    SchemaValidation,
    BusinessValidation,
    ReferenceValidation,
    ConfidenceValidation,
    ValidationPipeline,
    ValidationContext,
)

# Compiler Interface
from .compiler import (
    KnowledgeCompiler,
    CompilerConfig,
    compile_character,
    compile_scene,
    compile_glossary,
    compile_narrative,
    compile_style,
)

# Manifest
from .manifest import (
    KnowledgeManifest,
    ManifestBuilder,
    ManifestMetadata,
    build_knowledge_manifest,
)

# Confidence
from .confidence import (
    ConfidenceScore,
    ConfidenceCalculator,
    ConfidenceThresholds,
)

# Errors
from .errors import (
    KnowledgeExtractionError,
    SchemaValidationError,
    BusinessRuleViolationError,
    ReferenceResolutionError,
    ConfidenceThresholdError,
    CompilationError,
    ManifestGenerationError,
)

__all__ = [
    # Base Models
    "KnowledgeEntity",
    "ExtractionResult",
    "ValidationResult",
    "CompilationResult",
    "ExtractionContext",
    "EntityType",
    "ValidationSeverity",
    # Schema
    "KnowledgeSchema",
    "SchemaField",
    "SchemaValidator",
    "DomainSchema",
    "CHARACTER_SCHEMA",
    "GLOSSARY_SCHEMA",
    "SCENE_SCHEMA",
    "NARRATIVE_SCHEMA",
    "STYLE_SCHEMA",
    # Extractor Base
    "BaseKnowledgeExtractor",
    "ExtractionStrategy",
    "ExtractorConfig",
    # Validation Framework
    "ValidationRule",
    "SchemaValidation",
    "BusinessValidation",
    "ReferenceValidation",
    "ConfidenceValidation",
    "ValidationPipeline",
    "ValidationContext",
    # Compiler Interface
    "KnowledgeCompiler",
    "CompilerConfig",
    "compile_character",
    "compile_scene",
    "compile_glossary",
    "compile_narrative",
    "compile_style",
    # Manifest
    "KnowledgeManifest",
    "ManifestBuilder",
    "ManifestMetadata",
    "build_knowledge_manifest",
    # Confidence
    "ConfidenceScore",
    "ConfidenceCalculator",
    "ConfidenceThresholds",
    # Errors
    "KnowledgeExtractionError",
    "SchemaValidationError",
    "BusinessRuleViolationError",
    "ReferenceResolutionError",
    "ConfidenceThresholdError",
    "CompilationError",
    "ManifestGenerationError",
]

# Version
__version__ = "5.7.2"
__author__ = "NTPE Team"