# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence
# =====================================================

class TranslationMemoryError(Exception):
    """Base error for Translation Memory Intelligence."""


class TranslationMemoryInputError(TranslationMemoryError, ValueError):
    """Raised when a translation memory input is invalid."""
