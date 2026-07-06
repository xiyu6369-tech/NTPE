# =====================================================
# NTPE 1.2 Professional
# Stage-17.7 Production Runtime Integration
# =====================================================

class ProductionRuntimeError(Exception):
    """Base error for Stage-17.7 production runtime integration."""


class ProductionRuntimeInputError(ProductionRuntimeError):
    """Raised when production runtime input is invalid."""


class ProductionRuntimeBridgeError(ProductionRuntimeError):
    """Raised when a runtime bridge component fails."""
