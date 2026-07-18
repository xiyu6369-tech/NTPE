from __future__ import annotations


class GovernanceConsumptionError(Exception):
    """Base error with a stable, non-sensitive audit code."""

    status = "governance_baseline_consumption_invalid"

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class GovernanceBaselineInvalidError(GovernanceConsumptionError):
    pass


class GovernanceBaselineRejectedError(GovernanceConsumptionError):
    status = "governance_baseline_consumption_rejected"

