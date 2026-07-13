from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.adaptive_context_provider_evidence import ProviderEvidenceBundle

from .model import SESSION_VERSION, SessionSummary


@dataclass(frozen=True)
class ControlledSessionResult:
    summary: SessionSummary
    evidence: ProviderEvidenceBundle
    blockers: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    content_redacted: bool = True
    version: str = SESSION_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
