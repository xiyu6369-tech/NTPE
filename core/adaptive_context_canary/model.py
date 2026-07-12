from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

@dataclass(frozen=True)
class CanaryRecord:
    version: str
    package_id: str
    chunk_index: int
    target_chunk: int
    attempted: bool
    activated: bool
    fallback_used: bool
    fallback_reasons: tuple[str, ...]
    payload_hash_before: str
    payload_hash_after: str
    baseline_context_tokens: int
    canary_context_tokens: int
    estimated_tokens_saved: int
    latency_ms: float
    provider_calls_added: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)
    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_reasons", tuple(self.fallback_reasons))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
    def to_dict(self) -> dict[str, object]:
        return {"version":self.version,"package_id":self.package_id,"chunk_index":self.chunk_index,
        "target_chunk":self.target_chunk,"attempted":self.attempted,"activated":self.activated,
        "fallback_used":self.fallback_used,"fallback_reasons":list(self.fallback_reasons),
        "payload_hash_before":self.payload_hash_before,"payload_hash_after":self.payload_hash_after,
        "baseline_context_tokens":self.baseline_context_tokens,"canary_context_tokens":self.canary_context_tokens,
        "estimated_tokens_saved":self.estimated_tokens_saved,"latency_ms":self.latency_ms,
        "provider_calls_added":self.provider_calls_added,"metadata":dict(self.metadata)}
