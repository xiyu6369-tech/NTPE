"""
Knowledge Benchmark Runner (RM-5.8.3)

Offline benchmark pipeline that orchestrates:
    Golden Dataset -> Knowledge Extractor -> Validation -> Comparison -> Metrics -> Scorecard -> Regression Report

Zero provider API calls. Zero network requests.
Read-only access to Runtime and Translation Engine.
"""

from __future__ import annotations

from .loader import BenchmarkCorpusLoader
from .executor import ExtractionExecutor
from .report_writer import ReportWriter
from .runner import Runner

__all__ = [
    "BenchmarkCorpusLoader",
    "ExtractionExecutor",
    "ReportWriter",
    "Runner",
]

__version__ = "5.8.3"