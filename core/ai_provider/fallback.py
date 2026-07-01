from __future__ import annotations
from typing import Iterable, List

class FallbackStrategy:
    def __init__(self, providers: Iterable[str] = ()): 
        self.providers: List[str] = list(providers)
    def chain(self, preferred=None) -> List[str]:
        result = []
        if preferred:
            result.append(preferred)
        for p in self.providers:
            if p not in result:
                result.append(p)
        return result
