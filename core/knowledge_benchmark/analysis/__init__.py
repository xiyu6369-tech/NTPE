"""
Knowledge Benchmark Analysis Engine (RM-5.8.4)

Offline analysis layer that transforms benchmark results into actionable
improvement suggestions without modifying Runtime, Translation Engine,
Knowledge Package, or Provider.

Zero provider API calls. Zero network requests.
"""

from __future__ import annotations

from .models import (
    FailureCategory,
    FailureDetail,
    FailureSummary,
    RegressionStatus,
    RegressionResult,
    ExtractorStatistics,
    Suggestion,
    SuggestionReport,
    TrendDirection,
    TrendResult,
    AnalysisReport,
)
from .failure_classifier import FailureClassifier
from .regression_analyzer import RegressionAnalyzer
from .suggestion_engine import SuggestionEngine
from .statistics import StatisticsEngine
from .trend_analyzer import TrendAnalyzer

from .orchestrator import Analyzer, create_analyzer

__all__ = [
    "FailureCategory",
    "FailureDetail",
    "FailureSummary",
    "RegressionStatus",
    "RegressionResult",
    "ExtractorStatistics",
    "Suggestion",
    "SuggestionReport",
    "TrendDirection",
    "TrendResult",
    "AnalysisReport",
    "FailureClassifier",
    "RegressionAnalyser",
    "SuggestionEngine",
    "StatisticsEngine",
    "TrendAnalyzer",
    "Analyzer",
    "create_analyzer",
]

__version__ = "5.8.4"