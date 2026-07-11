from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptCompilerProfile:
    name: str = "literary"
    discipline_enabled: bool = False
    adaptive_enabled: bool = False
    budget_enabled: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "discipline_enabled": self.discipline_enabled,
            "adaptive_enabled": self.adaptive_enabled,
            "budget_enabled": self.budget_enabled,
        }
