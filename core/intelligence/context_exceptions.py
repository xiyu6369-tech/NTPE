# =====================================================
# NTPE 1.2 Professional
# Stage-16.1 Context Intelligence Engine
# =====================================================

class ContextIntelligenceError(Exception):
    """Base exception for Stage-16.1 Context Intelligence."""


class ContextWindowError(ContextIntelligenceError):
    """Raised when context window construction is invalid."""
