"""RM-7.1 Entity Consistency Runtime — public API.

Detect → Report → Review only.  Never mutates translations, knowledge,
or glossaries.  Read-only scanner + checker + reporter.
"""

from .checker import ConsistencyChecker
from .models import (
    ConsistencyReport,
    EntityCategory,
    EntityMatch,
    EntityMismatch,
    ReportSeverity,
)
from .report import ConsistencyReporter
from .scanner import EntityScanner

__all__ = [
    "EntityCategory",
    "EntityMatch",
    "EntityMismatch",
    "ConsistencyReport",
    "ReportSeverity",
    "EntityScanner",
    "ConsistencyChecker",
    "ConsistencyReporter",
]