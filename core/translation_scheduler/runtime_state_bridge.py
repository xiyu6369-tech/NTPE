from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class RuntimeSchedulerStateBridge:
    """Pure state bridge between runtime-shaped state and scheduler reports."""

    fallback_runtime_id = "runtime-state-unknown"

    def build_scheduler_snapshot(self, runtime_state: Mapping[str, Any] | None) -> dict[str, Any]:
        state = dict(runtime_state or {})
        chunks = self._extract_chunks(state)
        chunk_records = self._chunk_records(chunks)

        pending_chunks = self._indexes_by_status(chunk_records, {"pending", "queued", "running", "retry"})
        done_chunks = self._indexes_by_status(chunk_records, {"done", "completed", "success", "succeeded"})
        failed_chunks = self._indexes_by_status(chunk_records, {"failed", "failure", "error"})

        if not chunk_records:
            pending_chunks = self._list_field(state, "pending_chunks")
            done_chunks = self._list_field(state, "done_chunks")
            failed_chunks = self._list_field(state, "failed_chunks")

        chunks_total = self._chunks_total(state, pending_chunks, done_chunks, failed_chunks, len(chunk_records))
        merge_ready = chunks_total > 0 and len(done_chunks) == chunks_total and not pending_chunks and not failed_chunks

        return {
            "runtime_id": self._runtime_id(state),
            "chunks_total": chunks_total,
            "pending_chunks": pending_chunks,
            "done_chunks": done_chunks,
            "failed_chunks": failed_chunks,
            "merge_ready": merge_ready,
            "metadata": self._metadata(state),
        }

    def build_runtime_snapshot(self, scheduler_bundle: Mapping[str, Any] | None) -> dict[str, Any]:
        bundle = dict(scheduler_bundle or {})
        export_outputs = dict(bundle.get("export_outputs") or {})
        metadata = dict(bundle.get("metadata") or {})
        failed_chunk_report = list(bundle.get("failed_chunk_report") or export_outputs.get("failed_chunks") or [])
        merge_ready = bool(bundle.get("merge_ready", export_outputs.get("manifest", {}).get("merge_ready", False)))
        if failed_chunk_report:
            merge_ready = False

        return {
            "runtime_id": self._runtime_id(bundle),
            "scheduler_summary": dict(bundle.get("scheduler_summary") or {}),
            "collector_manifest": dict(bundle.get("collector_manifest") or export_outputs.get("manifest") or {}),
            "outputs_count": int(bundle.get("outputs_count", len(export_outputs.get("chunk_results", [])))),
            "merge_ready": merge_ready,
            "failed_chunk_report": failed_chunk_report,
            "metadata": {
                "bridge": "runtime_scheduler_state_bridge",
                "stage": "3.2.4",
                **metadata,
            },
        }

    def validate_snapshot(self, snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(snapshot or {})
        errors: list[str] = []

        if not isinstance(data.get("runtime_id"), str) or not data.get("runtime_id"):
            errors.append("runtime_id is required")
        if "merge_ready" not in data or not isinstance(data.get("merge_ready"), bool):
            errors.append("merge_ready boolean is required")
        if "metadata" not in data or not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")

        scheduler_shape = {"chunks_total", "pending_chunks", "done_chunks", "failed_chunks"}.issubset(data)
        runtime_shape = {"scheduler_summary", "collector_manifest", "outputs_count", "failed_chunk_report"}.issubset(data)
        if not scheduler_shape and not runtime_shape:
            errors.append("snapshot must be scheduler-shaped or runtime-shaped")

        if scheduler_shape:
            if not isinstance(data.get("chunks_total"), int):
                errors.append("chunks_total integer is required")
            for key in ("pending_chunks", "done_chunks", "failed_chunks"):
                if not isinstance(data.get(key), list):
                    errors.append(f"{key} list is required")

        if runtime_shape:
            if not isinstance(data.get("scheduler_summary"), Mapping):
                errors.append("scheduler_summary mapping is required")
            if not isinstance(data.get("collector_manifest"), Mapping):
                errors.append("collector_manifest mapping is required")
            if not isinstance(data.get("outputs_count"), int):
                errors.append("outputs_count integer is required")
            if not isinstance(data.get("failed_chunk_report"), list):
                errors.append("failed_chunk_report list is required")

        return {"valid": not errors, "errors": errors}

    def _extract_chunks(self, state: Mapping[str, Any]) -> list[Any]:
        chunks = state.get("chunks")
        if chunks is None:
            chunks = state.get("jobs")
        if chunks is None and isinstance(state.get("session"), Mapping):
            session = state["session"]
            chunks = session.get("chunks") or session.get("jobs")
        if isinstance(chunks, Sequence) and not isinstance(chunks, (str, bytes, bytearray)):
            return list(chunks)
        return []

    def _chunk_records(self, chunks: Sequence[Any]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for position, chunk in enumerate(chunks, start=1):
            if isinstance(chunk, Mapping):
                records.append(
                    {
                        "chunk_index": int(chunk.get("chunk_index", chunk.get("index", position))),
                        "status": str(chunk.get("status", "pending")).lower(),
                    }
                )
            else:
                records.append({"chunk_index": position, "status": "pending"})
        return records

    def _indexes_by_status(self, records: Sequence[Mapping[str, Any]], statuses: set[str]) -> list[int]:
        return sorted(int(record["chunk_index"]) for record in records if str(record.get("status", "")).lower() in statuses)

    def _list_field(self, state: Mapping[str, Any], key: str) -> list[int]:
        value = state.get(key, [])
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return []
        return sorted(int(item) for item in value)

    def _chunks_total(
        self,
        state: Mapping[str, Any],
        pending_chunks: Sequence[int],
        done_chunks: Sequence[int],
        failed_chunks: Sequence[int],
        observed_count: int,
    ) -> int:
        explicit = state.get("chunks_total")
        if explicit is not None:
            return int(explicit)
        observed = set(pending_chunks) | set(done_chunks) | set(failed_chunks)
        if observed:
            return max(observed)
        return observed_count

    def _runtime_id(self, state: Mapping[str, Any]) -> str:
        metadata = state.get("metadata") if isinstance(state.get("metadata"), Mapping) else {}
        value = state.get("runtime_id") or state.get("session_id") or state.get("job_id") or metadata.get("runtime_id")
        return str(value or self.fallback_runtime_id)

    def _metadata(self, state: Mapping[str, Any]) -> dict[str, Any]:
        metadata = dict(state.get("metadata") or {})
        metadata.setdefault("bridge", "runtime_scheduler_state_bridge")
        metadata.setdefault("stage", "3.2.4")
        return metadata


__all__ = ["RuntimeSchedulerStateBridge"]
