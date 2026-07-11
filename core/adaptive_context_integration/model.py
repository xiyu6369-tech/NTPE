from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Literal

ACEMode = Literal['disabled', 'shadow', 'active']

@dataclass(frozen=True)
class ACEIntegrationResult:
    version: str
    requested_mode: str
    effective_mode: ACEMode
    original_context: Mapping[str, object]
    effective_context: Mapping[str, object]
    prompt_payload: Mapping[str, object]
    prompt_payload_hash: str
    baseline_payload_hash: str
    used_ace: bool
    fallback_used: bool
    fallback_reasons: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'original_context', MappingProxyType(dict(self.original_context)))
        object.__setattr__(self, 'effective_context', MappingProxyType(dict(self.effective_context)))
        object.__setattr__(self, 'prompt_payload', MappingProxyType(dict(self.prompt_payload)))
        object.__setattr__(self, 'fallback_reasons', tuple(self.fallback_reasons))
        object.__setattr__(self, 'metrics', MappingProxyType(dict(self.metrics)))
