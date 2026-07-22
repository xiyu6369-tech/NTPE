class BookSegmentationError(ValueError):
    """Base error for invalid segmentation inputs and states."""


class InvalidSegmentationInputError(BookSegmentationError):
    """Raised when a public segmentation API receives an invalid input."""


class SegmentationInvariantError(BookSegmentationError):
    """Raised when lossless section invariants cannot be satisfied."""


class SourceFingerprintMismatchError(BookSegmentationError):
    """Raised when optional Intake manifest metadata does not match the text."""
