from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SessionStatistics:
    source_characters: int = 0
    translated_characters: int = 0
    chunk_total: int = 0
    file_total: int = 0
    success_count: int = 0
    failed_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
