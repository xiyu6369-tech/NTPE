from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class FallbackChain:
    providers: List[str] = field(default_factory=list)
    retry_escalation: bool = True
    stop_on_non_retryable: bool = True

    def resolve(self, candidates: Iterable[str]) -> List[str]:
        candidate_list = list(candidates)
        if not self.providers:
            return candidate_list
        ordered = [name for name in self.providers if name in candidate_list]
        ordered.extend(name for name in candidate_list if name not in ordered)
        return ordered

    def to_dict(self) -> Dict[str, object]:
        return {
            "providers": list(self.providers),
            "retry_escalation": self.retry_escalation,
            "stop_on_non_retryable": self.stop_on_non_retryable,
        }
