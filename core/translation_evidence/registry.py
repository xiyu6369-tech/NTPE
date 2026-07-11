from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from .evidence import TranslationEvidence

EvidenceDetector = Callable[[str, str], Iterable[TranslationEvidence]]


@dataclass
class EvidenceRegistry:
    _detectors: dict[str, EvidenceDetector] = field(default_factory=dict)

    def register(self, name: str, detector: EvidenceDetector, *, replace: bool = False) -> None:
        key = str(name or "").strip().lower()
        if not key:
            raise ValueError("detector name is required")
        if key in self._detectors and not replace:
            raise ValueError(f"detector already registered: {key}")
        self._detectors[key] = detector

    def get(self, name: str) -> EvidenceDetector:
        return self._detectors[str(name).strip().lower()]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._detectors))

    def items(self):
        return tuple((name, self._detectors[name]) for name in self.names())
