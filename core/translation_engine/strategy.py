"""Translation strategy objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class TranslationStrategy:
    name: str = "balanced"
    max_retries: int = 2
    enable_validation: bool = True
    enable_recovery: bool = True
    min_length_ratio: float = 0.05
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "max_retries": self.max_retries,
            "enable_validation": self.enable_validation,
            "enable_recovery": self.enable_recovery,
            "min_length_ratio": self.min_length_ratio,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def strict(cls) -> "TranslationStrategy":
        return cls(name="strict", max_retries=3, enable_validation=True, enable_recovery=True, min_length_ratio=0.1)

    @classmethod
    def fast(cls) -> "TranslationStrategy":
        return cls(name="fast", max_retries=1, enable_validation=True, enable_recovery=False, min_length_ratio=0.03)
