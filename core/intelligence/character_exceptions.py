# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

class CharacterIntelligenceError(Exception):
    """Base error for Character Relationship Intelligence."""


class CharacterInputError(CharacterIntelligenceError, ValueError):
    """Raised when character intelligence input is invalid."""
