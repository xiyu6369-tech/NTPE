# =====================================================
# NTPE 1.2 Professional
# Stage-17.4 Review & Approval Layer
# =====================================================

class ReviewError(Exception):
    """Base error for review and approval operations."""


class ReviewStateError(ReviewError):
    """Raised when an invalid review state transition is requested."""


class ApprovalGateError(ReviewError):
    """Raised when an approval gate cannot be evaluated."""
