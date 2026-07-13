from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

@dataclass(frozen=True)
class QualityEvidence:
    stage: str
    chunk: int
    source_hash: str
    accepted: bool
    status: str
    score: int
    issues: tuple[str, ...]
    source_chars: int
    translated_chars: int
    source_paragraphs: int
    translated_paragraphs: int
    length_ratio: float
    provider_complete: bool = True

@dataclass(frozen=True)
class CanaryABReport:
    version: str
    status: str
    ready: bool
    target_chunk: int
    baseline_stage: str
    canary_stage: str
    baseline_score: int
    canary_score: int
    baseline_accepted: bool
    canary_accepted: bool
    new_issues: tuple[str, ...]
    blockers: tuple[str, ...]
    limitations: tuple[str, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)
    def __post_init__(self) -> None:
        object.__setattr__(self, 'new_issues', tuple(self.new_issues))
        object.__setattr__(self, 'blockers', tuple(self.blockers))
        object.__setattr__(self, 'limitations', tuple(self.limitations))
        object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))
    def to_dict(self) -> dict[str, object]:
        return {
            'version': self.version, 'status': self.status, 'ready': self.ready,
            'target_chunk': self.target_chunk, 'baseline_stage': self.baseline_stage,
            'canary_stage': self.canary_stage, 'baseline_score': self.baseline_score,
            'canary_score': self.canary_score, 'baseline_accepted': self.baseline_accepted,
            'canary_accepted': self.canary_accepted, 'new_issues': list(self.new_issues),
            'blockers': list(self.blockers), 'limitations': list(self.limitations),
            'metadata': dict(self.metadata),
        }
