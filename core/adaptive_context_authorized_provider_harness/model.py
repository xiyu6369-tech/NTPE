from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.adaptive_context_real_provider_boundary import BoundaryInvocationResult

from .config import HARNESS_VERSION


@dataclass(frozen=True)
class AuthorizedProviderHarnessResult:
    session_id: str
    execution_provenance: str
    real_provider_execution: bool
    authorization_confirmed: bool
    boundary_enabled: bool
    real_provider_enabled: bool
    single_chunk_only: bool
    single_controlled_session: bool
    invocation: BoundaryInvocationResult
    request_persisted: bool = False
    prompt_persisted: bool = False
    response_body_persisted: bool = False
    credential_persisted: bool = False
    baseline_artifact_created: bool = False
    candidate_artifact_created: bool = False
    comparison_evaluated: bool = False
    readiness_evaluated: bool = False
    provider_automatically_executed: bool = False
    content_redacted: bool = True
    version: str = HARNESS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
