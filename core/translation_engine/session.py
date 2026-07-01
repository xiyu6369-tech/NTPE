"""Translation session state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import uuid


@dataclass
class TranslationSession:
    job_id: str = "translation-job"
    session_id: str = field(default_factory=lambda: f"trs-{uuid.uuid4().hex[:12]}")
    status: str = "created"
    current_index: int = 0
    total_segments: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def checkpoint(self) -> Dict[str, Any]:
        self.updated_at = time.time()
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "status": self.status,
            "current_index": self.current_index,
            "total_segments": self.total_segments,
            "result_count": len(self.results),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TranslationSessionManager:
    def __init__(self):
        self.current: Optional[TranslationSession] = None
        self.history: Dict[str, TranslationSession] = {}

    def create(self, job_id: str = "translation-job", total_segments: int = 0, metadata: Optional[Dict[str, Any]] = None) -> TranslationSession:
        session = TranslationSession(job_id=job_id, total_segments=total_segments, metadata=dict(metadata or {}))
        self.current = session
        self.history[session.session_id] = session
        return session

    def start(self) -> TranslationSession:
        if self.current is None:
            self.create()
        self.current.status = "running"
        self.current.updated_at = time.time()
        return self.current

    def record(self, index: int, result: Dict[str, Any]) -> TranslationSession:
        if self.current is None:
            self.create()
        self.current.current_index = index + 1
        self.current.results.append(dict(result))
        self.current.updated_at = time.time()
        return self.current

    def complete(self) -> TranslationSession:
        if self.current is None:
            self.create()
        self.current.status = "completed"
        self.current.updated_at = time.time()
        return self.current

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_session_manager", "active": self.current.to_dict() if self.current else None, "history_count": len(self.history)}
