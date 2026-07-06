# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, List


class CharacterMemory:
    """Cross-chunk memory for recently active characters and states."""

    def __init__(self, max_recent: int = 20) -> None:
        self.max_recent = max_recent
        self._recent: Deque[str] = deque(maxlen=max_recent)
        self._states: Dict[str, Dict[str, object]] = {}

    def observe(self, names: Iterable[str]) -> None:
        for name in names:
            if name:
                self._recent.append(name)

    def set_state(self, name: str, **state: object) -> None:
        if name:
            current = self._states.setdefault(name, {})
            current.update(state)

    def get_state(self, name: str) -> Dict[str, object]:
        return dict(self._states.get(name, {}))

    def recent(self) -> List[str]:
        return list(dict.fromkeys(self._recent))

    def to_dict(self) -> Dict[str, object]:
        return {"recent": self.recent(), "states": {key: dict(value) for key, value in self._states.items()}}
