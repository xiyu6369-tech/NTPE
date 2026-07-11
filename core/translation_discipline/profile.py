from __future__ import annotations

from dataclasses import dataclass

DISCIPLINE_PROFILES = ("strict_fidelity", "literary_balanced", "historical_literary", "modern_literary", "dialogue_heavy", "narration_heavy")
_ALIASES = {"literary": "literary_balanced", "balanced": "literary_balanced", "premium": "literary_balanced", "quality": "literary_balanced", "novel": "literary_balanced"}


def normalize_discipline_profile(profile: str | None) -> str:
    mapped = _ALIASES.get((profile or "literary").strip().lower(), (profile or "literary").strip().lower())
    return mapped if mapped in DISCIPLINE_PROFILES else "literary_balanced"


@dataclass(frozen=True)
class DisciplineProfile:
    name: str = "literary_balanced"

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_discipline_profile(self.name))
