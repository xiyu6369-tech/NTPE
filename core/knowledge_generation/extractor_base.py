"""Extractor Base Classes for Knowledge Extraction SDK v5.7.2
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from .models import (
    KnowledgeEntity,
    ExtractionResult,
    ExtractionContext,
    EntityType,
)
from .validator import ValidationPipeline, ValidationContext
from .compiler import get_compiler, CompilerConfig
from .manifest import KnowledgeManifest, build_knowledge_manifest
from .confidence import ConfidenceCalculator, DEFAULT_CALCULATOR
from .errors import (
    KnowledgeExtractionError,
    SchemaValidationError,
    ExtractionTimeoutError,
    ConfigurationError,
)


class ExtractionStrategy(str, Enum):
    CHUNK_BY_CHUNK = "chunk_by_chunk"
    WHOLE_DOCUMENT = "whole_document"
    SLIDING_WINDOW = "sliding_window"
    HIERARCHICAL = "hierarchical"


@dataclass
class ExtractorConfig:
    domain: str
    strategy: ExtractionStrategy = ExtractionStrategy.CHUNK_BY_CHUNK
    chunk_size: int = 2000
    chunk_overlap: int = 200
    max_entities_per_chunk: int = 50
    confidence_threshold: float = 0.3
    enable_validation: bool = True
    enable_compilation: bool = True
    custom_prompt_template: str = ""
    prompt_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")
        if self.chunk_overlap < 0:
            errors.append("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            errors.append("chunk_overlap must be less than chunk_size")
        if self.max_entities_per_chunk <= 0:
            errors.append("max_entities_per_chunk must be positive")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            errors.append("confidence_threshold must be between 0.0 and 1.0")
        return errors
class BaseKnowledgeExtractor(ABC):
    def __init__(self, config: ExtractorConfig):
        self.config = config
        self.domain = config.domain
        self._schema = None
        self._prompt_template = config.custom_prompt_template
        self._compiler = get_compiler(config.domain)
        self._validator = ValidationPipeline.create_default(config.domain)
        self._confidence_calculator = DEFAULT_CALCULATOR
        self._extraction_count = 0
        self._total_time_ms = 0.0

    @property
    @abstractmethod
    def schema(self):
        pass

    @property
    @abstractmethod
    def default_prompt(self) -> str:
        pass

    @property
    def prompt_template(self) -> str:
        return self._prompt_template or self.default_prompt

    def set_prompt_template(self, template: str) -> None:
        self._prompt_template = template

    def extract(self, context: ExtractionContext) -> ExtractionResult:
        return ExtractionResult.failure_result(["Not implemented"])

    @abstractmethod
    def _extract_chunk(self, context: ExtractionContext) -> ExtractionResult:
        pass

    def _chunk_document(self, text: str) -> List[str]:
        return [text]

    def normalize(self, entities: List[KnowledgeEntity]) -> List[KnowledgeEntity]:
        return entities

    def validate_entities(self, entities: List[KnowledgeEntity]) -> List[str]:
        return []

    def compile_entities(self, entities: List[KnowledgeEntity]) -> Dict[str, Any]:
        return {}

    def get_stats(self) -> Dict[str, Any]:
        return {"domain": self.domain, "extraction_count": 0, "total_time_ms": 0.0, "average_time_ms": 0.0}


def create_extractor(domain: str, config: ExtractorConfig = None) -> BaseKnowledgeExtractor:
    return BaseKnowledgeExtractor(config or ExtractorConfig(domain=domain))
