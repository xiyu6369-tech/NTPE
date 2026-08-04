"""
Knowledge Benchmark Metrics Engine (RM-5.8.2)

Offline scoring engine for evaluating Knowledge Extraction Layer quality.
Completely separated from Translation Runtime and Knowledge Runtime.

Zero dependencies on core/, lts/, or any runtime module.
Zero provider API calls. Zero network requests.
"""

from __future__ import annotations

from .models import (
    BenchmarkResult,
    BenchmarkMetadata,
    EntityMatchResult,
    ExtractionComparison,
    MetricScore,
    Scorecard,
    ExtractorScore,
    OverallScore,
    Grade,
)
from .errors import (
    BenchmarkError,
    GoldenDatasetError,
    ComparisonError,
    MetricComputationError,
    InvalidInputError,
)
from .scorer import BenchmarkScorer
from .comparison import ComparisonEngine

__all__ = [
    # Models
    "BenchmarkResult",
    "BenchmarkMetadata",
    "EntityMatchResult",
    "ExtractionComparison",
    "MetricScore",
    "Scorecard",
    "ExtractorScore",
    "OverallScore",
    "Grade",
    # Errors
    "BenchmarkError",
    "GoldenDatasetError",
    "ComparisonError",
    "MetricComputationError",
    "InvalidInputError",
    # Engine
    "BenchmarkScorer",
    "ComparisonEngine",
]

__version__ = "5.8.2"