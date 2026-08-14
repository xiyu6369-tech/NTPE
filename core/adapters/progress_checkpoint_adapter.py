from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChunkProgress:
    total: int
    completed: int
    failed: int
    skipped: int
    pending: int
    current_chunk: int | None
    current_step: str | None


@dataclass(frozen=True)
class ResumeState:
    version: str
    chunks: dict[str, dict[str, Any]]
    events: list[dict[str, Any]]
    input: str
    output_dir: str
    chunk_total: int
    updated_at: str


@dataclass(frozen=True)
class LiveProgress:
    status: str
    input: str
    output_dir: str
    chunk_total: int
    chunk_completed: int
    current_chunk: int | None
    current_step: str | None
    updated_at: str


class ProgressCheckpointAdapter:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def _find_stem(self, stem: str) -> Path | None:
        for p in self.output_dir.glob(f"{stem}_resume_state.json"):
            return p
        for p in self.output_dir.glob(f"*/{stem}_resume_state.json"):
            return p
        return None

    def get_resume_state(self, stem: str) -> ResumeState | None:
        path = self._find_stem(stem)
        if not path or not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
        return ResumeState(
            version=data.get("version", "unknown"),
            chunks=data.get("chunks", {}),
            events=data.get("events", []),
            input=data.get("input", ""),
            output_dir=data.get("output_dir", ""),
            chunk_total=data.get("chunk_total", 0),
            updated_at=data.get("updated_at", ""),
        )

    def get_live_progress(self, stem: str) -> LiveProgress | None:
        path = self._find_stem(stem)
        if not path:
            return None
        live_path = path.parent / f"{stem}_live_progress.json"
        if not live_path.exists():
            return None
        try:
            data = json.loads(live_path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
        return LiveProgress(
            status=data.get("status", "unknown"),
            input=data.get("input", ""),
            output_dir=data.get("output_dir", ""),
            chunk_total=data.get("chunk_total", 0),
            chunk_completed=data.get("chunk_completed", 0),
            current_chunk=data.get("current_chunk"),
            current_step=data.get("current_step"),
            updated_at=data.get("updated_at", ""),
        )

    def get_chunk_progress(self, resume_state: ResumeState) -> ChunkProgress:
        completed = 0
        failed = 0
        skipped = 0
        for chunk_data in resume_state.chunks.values():
            status = chunk_data.get("status", "")
            if status in ("success", "pass_with_warning"):
                completed += 1
            elif status in ("failed", "qa_failed"):
                failed += 1
            elif status == "skipped":
                skipped += 1
        total = resume_state.chunk_total
        pending = total - completed - failed - skipped
        current_chunk = None
        current_step = None
        for i in range(1, total + 1):
            key = f"{i:06d}"
            chunk_data = resume_state.chunks.get(key)
            if chunk_data and chunk_data.get("status") not in ("success", "pass_with_warning", "skipped"):
                current_chunk = i
                break
        return ChunkProgress(
            total=total,
            completed=completed,
            failed=failed,
            skipped=skipped,
            pending=pending,
            current_chunk=current_chunk,
            current_step=current_step,
        )