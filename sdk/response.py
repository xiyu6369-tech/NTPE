"""Stage-07.2 SDK Translation response objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TranslationResponse:
    """Stable response returned by the SDK Translation API."""

    ok: bool
    text: str = ""
    results: List[str] = field(default_factory=list)
    job_id: str = "sdk-translation-job"
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "text": self.text,
            "results": list(self.results),
            "job_id": self.job_id,
            "session_id": self.session_id,
            "data": dict(self.data),
            "errors": list(self.errors),
        }

    @classmethod
    def success(
        cls,
        results: List[str],
        *,
        job_id: str = "sdk-translation-job",
        session_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "TranslationResponse":
        text = results[0] if len(results) == 1 else "\n".join(results)
        return cls(ok=True, text=text, results=list(results), job_id=job_id, session_id=session_id, data=dict(data or {}))

    @classmethod
    def failure(cls, message: str, *, job_id: str = "sdk-translation-job", data: Optional[Dict[str, Any]] = None) -> "TranslationResponse":
        return cls(ok=False, job_id=job_id, data=dict(data or {}), errors=[str(message)])
