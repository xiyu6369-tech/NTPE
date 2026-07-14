from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.adaptive_context_provider_benchmark_session import ControlledSessionResult

from .config import BOUNDARY_VERSION


@dataclass(frozen=True)
class BoundaryInvocationResult:
    provider: str
    model: str
    execution_provenance: str
    real_provider_execution: bool
    authorization_recorded: bool
    credential_source: str
    session: ControlledSessionResult
    request_payload_persisted: bool = False
    comparison_evaluated: bool = False
    readiness_evaluated: bool = False
    content_redacted: bool = True
    version: str = BOUNDARY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
