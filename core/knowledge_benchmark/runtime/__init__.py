"""
Runtime Quality Gate Integration (RM-5.9.1)

Quality Observer that receives translation output, extracts knowledge,
runs benchmark evaluation, and produces a QualityDecision through the
existing RegressionGate + ReleaseGate pipeline.

Zero provider API calls. Zero network requests.
Does not modify Translation Engine core.
"""

from __future__ import annotations

from .models import (
    QualityDecision,
    QualityStatus,
    TranslationInput,
    KnowledgeExtractionOutput,
    GateInput,
)
from .adapter import RuntimeAdapter, create_runtime_adapter

__all__ = [
    "QualityDecision",
    "QualityStatus",
    "TranslationInput",
    "KnowledgeExtractionOutput",
    "GateInput",
    "RuntimeAdapter",
    "create_runtime_adapter",
]