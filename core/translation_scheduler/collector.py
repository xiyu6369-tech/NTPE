from __future__ import annotations

from typing import Any

from .job import JobStatus, TranslationJob, utc_now


class TranslationCollector:
    def __init__(self, chunks_total: int | None = None) -> None:
        self._results: dict[int, Any] = {}
        self._failures: dict[int, dict[str, Any]] = {}
        self._duplicates: list[dict[str, Any]] = []
        self._conflicts: set[int] = set()
        self._chunks_total = chunks_total
        self._updated_at = utc_now()

    def set_chunks_total(self, chunks_total: int) -> None:
        self._chunks_total = chunks_total
        self._touch()

    def collect(self, job: TranslationJob) -> bool:
        if job.status != JobStatus.DONE:
            return False
        if job.chunk_index in self._results:
            conflict = self._results[job.chunk_index] != job.result
            self._duplicates.append(
                {
                    "chunk_index": job.chunk_index,
                    "job_id": job.job_id,
                    "conflict": conflict,
                }
            )
            if conflict:
                self._conflicts.add(job.chunk_index)
            self._touch()
            return False
        self._results[job.chunk_index] = job.result
        self._touch()
        return True

    def collect_failure(self, job: TranslationJob) -> bool:
        if job.status != JobStatus.FAILED:
            return False
        if job.chunk_index in self._results or job.chunk_index in self._failures:
            self._duplicates.append(
                {
                    "chunk_index": job.chunk_index,
                    "job_id": job.job_id,
                    "conflict": False,
                    "status": job.status.value,
                }
            )
            self._touch()
            return False
        self._failures[job.chunk_index] = self._failure_record(job)
        self._touch()
        return True

    def get_result(self, chunk_index: int):
        return self._results.get(chunk_index)

    def get_failure(self, chunk_index: int):
        return self._failures.get(chunk_index)

    def has_result(self, chunk_index: int) -> bool:
        return chunk_index in self._results

    def has_failure(self, chunk_index: int) -> bool:
        return chunk_index in self._failures

    def merge_results(self, include_failed: bool = False) -> str:
        chunk_indexes = set(self._results)
        if include_failed:
            chunk_indexes.update(self._failures)
        merged: list[str] = []
        for chunk_index in sorted(chunk_indexes):
            if chunk_index in self._results:
                result = self._results[chunk_index]
                if result is not None:
                    merged.append(str(result))
            elif include_failed and chunk_index in self._failures:
                error = self._failures[chunk_index]["error"]
                merged.append(f"[FAILED chunk {chunk_index:04d}: {error}]")
        return "\n".join(merged)

    def build_manifest(self) -> dict[str, Any]:
        chunks_total = self._resolved_chunks_total()
        done_chunks = sorted(self._results)
        failed_chunks = sorted(self._failures)
        missing_chunks = [
            chunk_index
            for chunk_index in range(1, chunks_total + 1)
            if chunk_index not in self._results and chunk_index not in self._failures
        ]
        return {
            "chunks_total": chunks_total,
            "chunks_done": len(done_chunks),
            "chunks_failed": len(failed_chunks),
            "chunks_missing": len(missing_chunks),
            "chunk_order": list(range(1, chunks_total + 1)),
            "done_chunks": done_chunks,
            "failed_chunks": failed_chunks,
            "missing_chunks": missing_chunks,
            "duplicates": list(self._duplicates),
            "conflicts": sorted(self._conflicts),
            "merge_ready": chunks_total > 0 and not missing_chunks,
            "updated_at": self._updated_at.isoformat(),
        }

    def build_failed_chunk_report(self) -> list[dict[str, Any]]:
        return [self._failures[chunk_index] for chunk_index in sorted(self._failures)]

    def restore_audit(self, manifest: dict[str, Any]) -> None:
        self._duplicates = list(manifest.get("duplicates", []))
        self._conflicts = set(manifest.get("conflicts", []))
        if "chunks_total" in manifest:
            self._chunks_total = int(manifest["chunks_total"])
        self._touch()

    def duplicate_count(self) -> int:
        return len(self._duplicates)

    def collected_count(self) -> int:
        return len(self._results)

    def failed_count(self) -> int:
        return len(self._failures)

    def conflict_count(self) -> int:
        return len(self._conflicts)

    def merge_ready(self) -> bool:
        return bool(self.build_manifest()["merge_ready"])

    def _failure_record(self, job: TranslationJob) -> dict[str, Any]:
        return {
            "chunk_index": job.chunk_index,
            "job_id": job.job_id,
            "error": job.error or job.last_error or "",
            "attempts": job.attempts,
            "retry_count": job.retry_count,
            "error_history": list(job.error_history),
            "status": job.status.value,
        }

    def _resolved_chunks_total(self) -> int:
        observed = set(self._results) | set(self._failures)
        if self._chunks_total is not None:
            return self._chunks_total
        return max(observed, default=0)

    def _touch(self) -> None:
        self._updated_at = utc_now()
