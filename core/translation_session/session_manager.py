from __future__ import annotations

from pathlib import Path
from typing import Any

from .session import TranslationSession
from .session_checkpoint import load_checkpoint


class TranslationSessionManager:
    """Factory and lifecycle manager for NTPE Professional translation sessions."""

    version = "1.2-professional-stage-05"

    def __init__(self, root: str | Path, runtime: Any):
        self.root = Path(root)
        self.runtime = runtime

    @property
    def sessions_dir(self) -> Path:
        return self.root / ".ntpe_sessions"

    def create_session(self, mode: str = "runtime", input_source: str = "", output_target: str = "", metadata: dict[str, Any] | None = None) -> TranslationSession:
        session = TranslationSession(
            root=self.root,
            runtime=self.runtime,
            mode=mode,
            input_source=input_source,
            output_target=output_target,
            metadata=metadata or {},
        )
        session.create()
        return session

    def get_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        checkpoint = load_checkpoint(self.root, session_id)
        return checkpoint.to_dict() if checkpoint else None

    def list_sessions(self) -> dict[str, Any]:
        if not self.sessions_dir.exists():
            return {"status": "success", "total": 0, "sessions": []}
        sessions: list[dict[str, Any]] = []
        for path in sorted(self.sessions_dir.glob("*/session_checkpoint.json")):
            checkpoint = load_checkpoint(self.root, path.parent.name)
            if checkpoint:
                sessions.append(checkpoint.to_dict())
        return {"status": "success", "total": len(sessions), "sessions": sessions}
