# =====================================================
# NTPE 1.2 Professional
# Stage-16.7 Intelligence Runtime Integration
# =====================================================

class IntelligenceRuntimeError(Exception):
    """Base error for Intelligence Runtime Integration."""


class IntelligenceRuntimeInputError(IntelligenceRuntimeError):
    """Raised when runtime intelligence input is invalid."""
