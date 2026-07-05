from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .session_checkpoint import SessionCheckpoint, save_checkpoint
from .session_manifest import SessionManifest
from .session_state import SessionState
from .session_statistics import SessionStatistics


@dataclass
class TranslationSession:
    """Formal session lifecycle wrapper for TranslationRuntime.

    The class is intentionally additive. It does not replace LTS resume files or
    Runtime checkpoints; it adds a stable Professional session envelope above
    them for future CLI, Web UI, SDK, and API layers.
    """

    root: Path
    runtime: Any
    mode: str = "runtime"
    input_source: str = ""
    output_target: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: uuid4().hex)
    state: SessionState = field(default_factory=SessionState)
    statistics: SessionStatistics = field(default_factory=SessionStatistics)

    @property
    def session_dir(self) -> Path:
        return self.root / ".ntpe_sessions" / self.session_id

    def manifest(self) -> SessionManifest:
        return SessionManifest(
            session_id=self.session_id,
            root=str(self.root),
            runtime_version=getattr(self.runtime, "version", "unknown"),
            input_source=self.input_source,
            output_target=self.output_target,
            mode=self.mode,
            metadata=dict(self.metadata),
        )

    def create(self) -> dict[str, Any]:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.manifest().save()
        self.state.resume_token = self.session_id
        self.save_checkpoint()
        return {"status": "success", "session_id": self.session_id, "manifest_path": str(manifest_path)}

    def save_checkpoint(self) -> dict[str, Any]:
        checkpoint = SessionCheckpoint(
            session_id=self.session_id,
            status=self.state.status,
            cursor=self.state.to_dict(),
            statistics=self.statistics.to_dict(),
            error=self.state.last_error,
        )
        path = save_checkpoint(self.root, checkpoint)
        return {"status": "success", "checkpoint_path": str(path), "session_id": self.session_id}

    def execute(self, operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if not self.session_dir.exists():
            self.create()
        self.state.mark_running()
        self.save_checkpoint()
        try:
            result = operation()
            if result.get("status") == "success":
                self._absorb_result(result)
                self.state.mark_completed()
            else:
                self.state.mark_failed(str(result.get("error", "session operation failed")))
            self.save_checkpoint()
            return {"status": self.state.status, "session_id": self.session_id, "result": result, "statistics": self.statistics.to_dict()}
        except Exception as exc:  # defensive session envelope for future provider errors
            self.state.mark_failed(str(exc))
            self.save_checkpoint()
            return {"status": "failed", "session_id": self.session_id, "error": str(exc), "statistics": self.statistics.to_dict()}

    def _absorb_result(self, result: dict[str, Any]) -> None:
        if "chunk_total" in result:
            self.statistics.chunk_total = int(result.get("chunk_total") or 0)
            self.state.progress_total = self.statistics.chunk_total
        summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
        if summary:
            self.statistics.file_total = int(summary.get("total_files") or 0)
            self.statistics.success_count = int(summary.get("success") or 0)
            self.statistics.failed_count = int(summary.get("failed") or 0)
            self.state.progress_total = self.statistics.file_total
            self.state.progress_current = self.statistics.success_count + self.statistics.failed_count
        elif self.state.progress_total:
            self.state.progress_current = self.state.progress_total
