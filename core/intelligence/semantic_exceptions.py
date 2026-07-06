# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

class SemanticIntelligenceError(Exception):
    """Base exception for semantic consistency intelligence."""


class SemanticInputError(SemanticIntelligenceError):
    """Raised when semantic analysis input is invalid."""
