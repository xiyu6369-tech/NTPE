from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from .dashboard import PerformanceDashboard
from .job import JobStatus, TranslationJob
from .scheduler import TranslationScheduler


class RuntimeSchedulerAdapter:
    """Adapter skeleton for future runtime use of the TE-v3.1 scheduler."""

    def __init__(self, default_max_attempts: int = 2) -> None:
        self.default_max_attempts = default_max_attempts

    def create_scheduler_from_chunks(
        self,
        chunks: Sequence[str],
        packages: Sequence[Any] | dict[int, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TranslationScheduler:
        scheduler = TranslationScheduler(default_max_attempts=self.default_max_attempts)
        jobs = [
            self.create_job_package(
                chunk,
                package=self._package_for(packages, offset, offset + 1),
                chunk_index=offset + 1,
                metadata=metadata,
            )
            for offset, chunk in enumerate(chunks)
        ]
        for job in jobs:
            scheduler.queue.enqueue(job)
        scheduler.collector.set_chunks_total(len(jobs))
        return scheduler

    def create_job_package(
        self,
        chunk: str,
        package: Any = None,
        chunk_index: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> TranslationJob:
        job = TranslationJob(
            job_id=f"runtime-adapter-job-{chunk_index:06d}",
            chunk_index=chunk_index,
            source_text=chunk,
            package=package,
            max_attempts=self.default_max_attempts,
        )
        job.metadata = dict(metadata or {})
        return job

    def run_with_handler(
        self,
        chunks: Sequence[str],
        handler: Callable[[TranslationJob], Any] | None = None,
        packages: Sequence[Any] | dict[int, Any] | None = None,
    ) -> TranslationScheduler:
        scheduler = self.create_scheduler_from_chunks(chunks, packages=packages)
        scheduler.run(self._handler_wrapper(handler or self._mock_handler))
        return scheduler

    def run_with_scheduler(
        self,
        chunks: Sequence[Any],
        scheduler: TranslationScheduler,
        handler: Callable[[TranslationJob], Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_chunk_index = self._last_chunk_index(scheduler)
        for offset, chunk in enumerate(chunks):
            chunk_index = base_chunk_index + offset + 1
            job = self.create_job_package(
                self._chunk_text(chunk),
                package=chunk,
                chunk_index=chunk_index,
                metadata=self._chunk_metadata(chunk, metadata),
            )
            scheduler.queue.enqueue(job)
        scheduler.collector.set_chunks_total(len(scheduler.queue.all_jobs()))
        scheduler.run(self._handler_wrapper(handler or self._mock_handler))
        return self._runtime_bundle(scheduler, require_all_done=True)

    def build_runtime_report(self, scheduler: TranslationScheduler) -> dict[str, Any]:
        manifest = scheduler.collector.build_manifest()
        failed_chunk_report = scheduler.collector.build_failed_chunk_report()
        return {
            "scheduler_summary": scheduler.summary(),
            "collector_manifest": manifest,
            "failed_chunk_report": failed_chunk_report,
            "dashboard_report": PerformanceDashboard().build_report(scheduler),
            "outputs_count": scheduler.collector.collected_count(),
            "merge_ready": manifest["merge_ready"],
        }

    def export_outputs(self, scheduler: TranslationScheduler) -> dict[str, Any]:
        manifest = scheduler.collector.build_manifest()
        return {
            "merged_text": scheduler.collector.merge_results(),
            "chunk_results": self._chunk_results(scheduler),
            "failed_chunks": scheduler.collector.build_failed_chunk_report(),
            "manifest": manifest,
        }

    def _handler_wrapper(self, handler: Callable[[TranslationJob], Any]) -> Callable[[TranslationJob], Any]:
        def wrapped(job: TranslationJob) -> Any:
            result = handler(job)
            return self._normalize_handler_result(job, result)

        return wrapped

    def _normalize_handler_result(self, job: TranslationJob, result: Any) -> Any:
        if isinstance(result, dict):
            job.handler_result = dict(result)
            job.result_metadata = dict(result.get("metadata") or {})
            if "text" in result:
                return result["text"]
        return result

    def _chunk_results(self, scheduler: TranslationScheduler) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for job in scheduler.queue.all_jobs():
            if job.status == JobStatus.DONE:
                results.append(
                    {
                        "chunk_index": job.chunk_index,
                        "job_id": job.job_id,
                        "text": job.result,
                        "metadata": dict(getattr(job, "result_metadata", {})),
                    }
                )
        return sorted(results, key=lambda item: item["chunk_index"])

    def _mock_handler(self, job: TranslationJob) -> str:
        return job.source_text

    def _runtime_bundle(self, scheduler: TranslationScheduler, require_all_done: bool = False) -> dict[str, Any]:
        report = self.build_runtime_report(scheduler)
        if require_all_done:
            report["merge_ready"] = bool(report["merge_ready"] and scheduler.queue.failed_count() == 0)
        report["export_outputs"] = self.export_outputs(scheduler)
        return report

    def _last_chunk_index(self, scheduler: TranslationScheduler) -> int:
        existing = [job.chunk_index for job in scheduler.queue.all_jobs()]
        return max(existing) if existing else 0

    def _chunk_text(self, chunk: Any) -> str:
        if isinstance(chunk, dict):
            return str(chunk.get("text", chunk.get("source_text", "")))
        return str(chunk)

    def _chunk_metadata(self, chunk: Any, metadata: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(metadata or {})
        if isinstance(chunk, dict):
            merged.update(dict(chunk.get("metadata") or {}))
        return merged

    def _package_for(self, packages: Sequence[Any] | dict[int, Any] | None, offset: int, chunk_index: int) -> Any:
        if packages is None:
            return None
        if isinstance(packages, dict):
            return packages.get(chunk_index, packages.get(offset))
        return packages[offset] if offset < len(packages) else None


__all__ = ["RuntimeSchedulerAdapter"]
