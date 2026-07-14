from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DefectLocation:
    artifact: str
    locator: str

    def __post_init__(self) -> None:
        if not self.artifact.strip() or not self.locator.strip():
            raise ValueError("defect location requires artifact and locator")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
