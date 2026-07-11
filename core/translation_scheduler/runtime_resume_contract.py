from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeSchedulerResumeContract:
    """Build and validate safe resume plans from runtime scheduler snapshots."""

    fallback_runtime_id = "runtime-state-unknown"

    def build_resume_plan(self, snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(snapshot or {})
        metadata = dict(data.get("metadata") or {})
        pending_chunks = self._chunk_list(data, "pending_chunks")
        done_chunks = self._chunk_list(data, "done_chunks")
        failed_chunks = self._chunk_list(data, "failed_chunks")

        collector_manifest = data.get("collector_manifest")
        if isinstance(collector_manifest, Mapping):
            pending_chunks = pending_chunks or self._chunk_list(collector_manifest, "missing_chunks")
            done_chunks = done_chunks or self._chunk_list(collector_manifest, "done_chunks")
            failed_chunks = failed_chunks or self._chunk_list(collector_manifest, "failed_chunks")

        if not failed_chunks:
            failed_chunks = self._failed_report_chunks(data.get("failed_chunk_report"))

        chunks_total = self._chunks_total(data, pending_chunks, done_chunks, failed_chunks)
        merge_ready = bool(data.get("merge_ready", False))
        resume_chunks = sorted(set(pending_chunks) | set(failed_chunks))
        skip_chunks = sorted(set(done_chunks))
        resumable, reason = self._resume_status(chunks_total, merge_ready, resume_chunks)

        return {
            "runtime_id": self._runtime_id(data),
            "chunks_total": chunks_total,
            "resume_chunks": resume_chunks,
            "skip_chunks": skip_chunks,
            "failed_chunks": sorted(set(failed_chunks)),
            "merge_ready": merge_ready,
            "resumable": resumable,
            "reason": reason,
            "metadata": {
                "contract": "runtime_scheduler_resume_contract",
                "stage": "3.2.5",
                **metadata,
            },
        }

    def validate_resume_plan(self, plan: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(plan or {})
        errors: list[str] = []

        if not isinstance(data.get("runtime_id"), str) or not data.get("runtime_id"):
            errors.append("runtime_id is required")
        if not isinstance(data.get("chunks_total"), int):
            errors.append("chunks_total integer is required")
        for key in ("resume_chunks", "skip_chunks", "failed_chunks"):
            if not isinstance(data.get(key), list):
                errors.append(f"{key} list is required")
        for key in ("merge_ready", "resumable"):
            if not isinstance(data.get(key), bool):
                errors.append(f"{key} boolean is required")
        if not isinstance(data.get("reason"), str) or not data.get("reason"):
            errors.append("reason is required")
        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        return {"valid": not errors, "errors": errors}

    def _chunk_list(self, data: Mapping[str, Any], key: str) -> list[int]:
        value = data.get(key, [])
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return []
        return sorted(int(item) for item in value)

    def _failed_report_chunks(self, failed_chunk_report: Any) -> list[int]:
        if not isinstance(failed_chunk_report, Sequence) or isinstance(failed_chunk_report, (str, bytes, bytearray)):
            return []
        chunks: list[int] = []
        for item in failed_chunk_report:
            if isinstance(item, Mapping) and item.get("chunk_index") is not None:
                chunks.append(int(item["chunk_index"]))
        return sorted(chunks)

    def _chunks_total(
        self,
        data: Mapping[str, Any],
        pending_chunks: Sequence[int],
        done_chunks: Sequence[int],
        failed_chunks: Sequence[int],
    ) -> int:
        explicit = data.get("chunks_total")
        if explicit is not None:
            return int(explicit)
        collector_manifest = data.get("collector_manifest")
        if isinstance(collector_manifest, Mapping) and collector_manifest.get("chunks_total") is not None:
            return int(collector_manifest["chunks_total"])
        observed = set(pending_chunks) | set(done_chunks) | set(failed_chunks)
        return max(observed, default=0)

    def _runtime_id(self, data: Mapping[str, Any]) -> str:
        metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}
        value = data.get("runtime_id") or data.get("session_id") or data.get("job_id") or metadata.get("runtime_id")
        return str(value or self.fallback_runtime_id)

    def _resume_status(self, chunks_total: int, merge_ready: bool, resume_chunks: Sequence[int]) -> tuple[bool, str]:
        if chunks_total == 0:
            return False, "no_chunks"
        if merge_ready and not resume_chunks:
            return False, "already_complete"
        if resume_chunks:
            return True, "resume_required"
        return False, "not_resumable"


__all__ = ["RuntimeSchedulerResumeContract"]
