"""
Knowledge Benchmark Metrics Engine (RM-5.8.5)

Offline scoring, analysis, dashboard, baseline management, regression gate,
and release gate for the Knowledge Extraction Layer.

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
from .regression_gate import RegressionGate, RegressionGateReport, GateStatus, create_regression_gate
from .release_gate import ReleaseGate, ReleaseGateResult, ReleaseDecision, create_release_gate
from .dashboard import DashboardGenerator, DashboardModel, DashboardSlot, create_dashboard_generator
from .baseline import BaselineManager, BaselineEntry, BaselineIndex, create_baseline_manager

__all__ = [
    "BenchmarkResult",
    "BenchmarkMetadata",
    "EntityMatchResult",
    "ExtractionComparison",
    "MetricScore",
    "Scorecard",
    "ExtractorScore",
    "OverallScore",
    "Grade",
    "BenchmarkError",
    "GoldenDatasetError",
    "ComparisonError",
    "MetricComputationError",
    "InvalidInputError",
    "BenchmarkScorer",
    "ComparisonEngine",
    "RegressionGate",
    "RegressionGateReport",
    "GateStatus",
    "create_regression_gate",
    "ReleaseGate",
    "ReleaseGateResult",
    "ReleaseDecision",
    "create_release_gate",
    "DashboardGenerator",
    "DashboardModel",
    "DashboardSlot",
    "create_dashboard_generator",
    "BaselineManager",
    "BaselineEntry",
    "BaselineIndex",
    "create_baseline_manager",
]

__version__ = "5.8.5"