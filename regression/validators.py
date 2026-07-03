"""Regression validation primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict

@dataclass(frozen=True)
class RegressionCheck:
    name: str
    category: str
    fn: Callable[[], bool]

    def run(self) -> Dict[str, object]:
        try:
            passed = bool(self.fn())
            error = None
        except Exception as exc:  # pragma: no cover
            passed = False
            error = str(exc)
        return {"name": self.name, "category": self.category, "status": "PASS" if passed else "FAIL", "error": error}

def always_pass() -> bool:
    return True
