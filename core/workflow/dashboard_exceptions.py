# =====================================================
# NTPE 1.2 Professional
# Stage-17.6 Monitoring Dashboard API
# =====================================================

class DashboardError(Exception):
    """Base dashboard API error."""


class DashboardSourceError(DashboardError):
    """Raised when a dashboard source cannot be normalized."""
