# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer
# =====================================================

from __future__ import annotations


class ResourceOptimizerError(Exception):
    """Base error for Stage-17.3 resource optimization."""


class ResourceBudgetError(ResourceOptimizerError):
    """Raised when a resource budget is invalid or exceeded."""
