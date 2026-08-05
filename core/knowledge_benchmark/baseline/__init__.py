"""
Baseline Manager (RM-5.8.5)

Manages benchmark baselines for regression comparison.
Provides promote, rollback, list, and load operations.

Offline. Zero external dependencies. Read-only on Runtime/Translation/Knowledge.
"""

from __future__ import annotations

from .models import (
    BaselineEntry,
    BaselineIndex,
    BaselineStatus,
    BaselineRecord,
)
from .storage import BaselineStorage
from .manager import BaselineManager, create_baseline_manager

__all__ = [
    "BaselineEntry",
    "BaselineIndex",
    "BaselineStatus",
    "BaselineRecord",
    "BaselineStorage",
    "BaselineManager",
    "create_baseline_manager",
]

__version__ = "5.8.5"