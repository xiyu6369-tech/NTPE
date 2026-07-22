class BookChunkingError(ValueError):
    """Base error for invalid deterministic chunk planning operations."""


class InvalidChunkPolicyError(BookChunkingError):
    """Raised when chunk size parameters or policy values are invalid."""


class ChunkPlanningInvariantError(BookChunkingError):
    """Raised when a lossless chunk plan cannot satisfy its invariants."""


class SegmentationConsistencyError(BookChunkingError):
    """Raised when an input segmentation result fails closed validation."""
