from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CLIResult:
    """Structured result returned by NTPE CLI commands."""

    exit_code: int = 0
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "exit_code": self.exit_code,
            "message": self.message,
            "data": dict(self.data),
            "errors": list(self.errors),
        }

    @classmethod
    def success(cls, message: str = "", **data: Any) -> "CLIResult":
        return cls(exit_code=0, message=message, data=dict(data))

    @classmethod
    def failure(cls, message: str, exit_code: int = 1, errors: Optional[List[str]] = None, **data: Any) -> "CLIResult":
        return cls(exit_code=exit_code, message=message, data=dict(data), errors=errors or [message])
