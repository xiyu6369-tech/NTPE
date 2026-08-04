"""
Benchmark Metrics Package (RM-5.8.2)

Metric computation modules for Knowledge Benchmark.
All metrics are deterministic, offline, and follow RM-5.8.0 METRICS specification.
"""

from __future__ import annotations

from .accuracy import AccuracyMetric, ExactMatchAccuracy, FieldLevelAccuracy, EntityLevelAccuracy
from .precision import PrecisionMetric
from .recall import RecallMetric
from .f1_score import F1ScoreMetric
from .confidence_metrics import (
    ConfidenceCalibrationMetric,
    ExpectedCalibrationError,
    FalseHighConfidenceRate,
    FalseLowConfidenceRate,
)
from .schema_compliance import SchemaComplianceMetric, BusinessRuleComplianceMetric, ReviewComplianceMetric

__all__ = [
    "AccuracyMetric",
    "ExactMatchAccuracy",
    "FieldLevelAccuracy",
    "EntityLevelAccuracy",
    "PrecisionMetric",
    "RecallMetric",
    "F1ScoreMetric",
    "ConfidenceCalibrationMetric",
    "ExpectedCalibrationError",
    "FalseHighConfidenceRate",
    "FalseLowConfidenceRate",
    "SchemaComplianceMetric",
    "BusinessRuleComplianceMetric",
    "ReviewComplianceMetric",
]

__version__ = "5.8.2"