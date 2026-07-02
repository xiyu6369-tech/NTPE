from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List

FOUNDATION_VERSION = "1.0"
FOUNDATION_STATUS = "Frozen"
FOUNDATION_API_LEVEL = 1
FOUNDATION_COMPATIBILITY = "Stable"
FOUNDATION_BASELINE_NAME = "NTPE Foundation v1.0"

FROZEN_CONTRACTS: List[str] = [
    "runtime",
    "context_pipeline",
    "prompt_pipeline",
    "plugin_system",
    "production_pipeline",
    "translation_runtime",
    "intelligence",
    "knowledge",
    "snapshot",
]

@dataclass(frozen=True)
class FoundationBaseline:
    name: str = FOUNDATION_BASELINE_NAME
    version: str = FOUNDATION_VERSION
    status: str = FOUNDATION_STATUS
    api_level: int = FOUNDATION_API_LEVEL
    compatibility: str = FOUNDATION_COMPATIBILITY
    frozen_contracts: List[str] = None

    def __post_init__(self) -> None:
        if self.frozen_contracts is None:
            object.__setattr__(self, "frozen_contracts", list(FROZEN_CONTRACTS))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_foundation_baseline() -> FoundationBaseline:
    return FoundationBaseline()


def get_foundation_version() -> str:
    return FOUNDATION_VERSION


def is_foundation_frozen() -> bool:
    return FOUNDATION_STATUS.lower() == "frozen"
