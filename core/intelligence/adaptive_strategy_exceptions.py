# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

class AdaptiveStrategyError(Exception):
    """Base error for adaptive translation strategy."""


class AdaptiveStrategyInputError(AdaptiveStrategyError):
    """Raised when strategy input is invalid."""
