# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

class NarrativeIntelligenceError(Exception):
    """Base exception for the Stage-16.2 narrative intelligence layer."""


class NarrativeInputError(NarrativeIntelligenceError):
    """Raised when narrative analysis receives invalid input."""
