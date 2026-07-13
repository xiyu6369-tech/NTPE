from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class TEV6ReleaseContract:
    version: str
    channel: str
    frozen: bool
    discipline_frozen: bool
    evidence_frozen: bool
    naturalness_frozen: bool
    provider_contract_frozen: bool
    prompt_contract_frozen: bool
    quality_contract_frozen: bool
    retry_contract_frozen: bool
    resume_contract_frozen: bool
    backward_compatible: bool
    production_validated: bool
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            name: (dict(value) if name == "metadata" else value)
            for name, value in vars(self).items()
        }
