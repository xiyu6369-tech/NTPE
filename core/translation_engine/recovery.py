"""Translation recovery manager."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class TranslationRecoveryResult:
    success: bool
    attempts: int
    output: Any = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"success": self.success, "attempts": self.attempts, "output": self.output, "errors": list(self.errors)}


class TranslationRecoveryManager:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.last_result = TranslationRecoveryResult(success=True, attempts=0)

    def run(self, fn: Callable[[], Any]) -> Any:
        errors: List[str] = []
        attempts = 0
        for attempt in range(self.max_retries + 1):
            attempts = attempt + 1
            try:
                output = fn()
                self.last_result = TranslationRecoveryResult(True, attempts, output, errors)
                return output
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
        self.last_result = TranslationRecoveryResult(False, attempts, None, errors)
        raise RuntimeError("translation recovery exhausted: " + " | ".join(errors))

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_recovery", "max_retries": self.max_retries, "last_result": self.last_result.to_dict()}
