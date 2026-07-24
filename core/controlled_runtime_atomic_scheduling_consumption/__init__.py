"""Stage 6.7 — Atomic Scheduling Authorization Consumption.

Consume exactly one authentic Stage 6.6 scheduling authorization decision.
Produce one durable, immutable, single-use scheduling-consumption claim.
Do NOT schedule, enqueue, create a job, start a worker, invoke Runtime,
call Provider, access Network, or translate.
"""

from .consumer import AtomicSchedulingAuthorizationConsumer
from .models import (
    AtomicSchedulingAuthorizationConsumptionClaim,
    AtomicSchedulingAuthorizationConsumptionRequest,
    AtomicSchedulingAuthorizationConsumptionResult,
)
from .policy import AtomicSchedulingAuthorizationConsumptionPolicy
from .registry import AtomicSchedulingAuthorizationConsumptionRegistry
from .verification import verify_atomic_scheduling_consumption_claim

__all__ = [
    "AtomicSchedulingAuthorizationConsumptionRequest",
    "AtomicSchedulingAuthorizationConsumptionClaim",
    "AtomicSchedulingAuthorizationConsumptionResult",
    "AtomicSchedulingAuthorizationConsumptionPolicy",
    "AtomicSchedulingAuthorizationConsumptionRegistry",
    "AtomicSchedulingAuthorizationConsumer",
    "verify_atomic_scheduling_consumption_claim",
]