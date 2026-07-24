"""Stage 6.4 — Controlled Runtime Execution Envelope

Creates a deterministic, immutable, fail-closed envelope binding one authentic
Stage 6.3 durable claim to one exact controlled Runtime execution handoff contract.

Public API:
- ControlledRuntimeExecutionEnvelopeRequest
- ControlledRuntimeExecutionEnvelope
- ControlledRuntimeExecutionEnvelopeResult
- ControlledRuntimeExecutionEnvelopePolicy
- ControlledRuntimeExecutionEnvelopeBuilder
- verify_execution_envelope
"""

from .builder import ControlledRuntimeExecutionEnvelopeBuilder
from .models import (
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelopeResult,
)
from .policy import ControlledRuntimeExecutionEnvelopePolicy
from .verification import verify_execution_envelope

__all__ = (
    "ControlledRuntimeExecutionEnvelopeRequest",
    "ControlledRuntimeExecutionEnvelope",
    "ControlledRuntimeExecutionEnvelopeResult",
    "ControlledRuntimeExecutionEnvelopePolicy",
    "ControlledRuntimeExecutionEnvelopeBuilder",
    "verify_execution_envelope",
)