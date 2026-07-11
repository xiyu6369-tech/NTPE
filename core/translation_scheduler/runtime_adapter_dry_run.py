"""
TE v3.2 Stage-3.2.2 Runtime Adapter Dry Run.

This module adds a dry-run harness around the Stage-3.2.1
RuntimeSchedulerAdapter contract.

Stage guarantees:
- Does not modify Provider Runtime.
- Does not call HTTP/client APIs.
- Does not read or write API keys.
- Does not modify launcher_translate.py.
- Does not execute real translation.
- Uses mock chunk handlers only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .scheduler import TranslationScheduler


ChunkHandler = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class RuntimeAdapterDryRunResult:
    """Dry-run output bundle for validation and regression tests."""

    scheduler_summary: Dict[str, Any]
    collector_manifest: Dict[str, Any]
    failed_chunk_report: List[Dict[str, Any]]
    dashboard_report: Dict[str, Any]
    outputs_count: int
    merge_ready: bool
    export_outputs: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuntimeAdapterDryRun:
    """
    Safe dry-run wrapper for RuntimeSchedulerAdapter.

    The wrapper accepts the existing Stage-3.2.1 adapter, but does not require
    changing the adapter schema. If the adapter exposes a compatible
    ``run_with_handler`` method, this harness delegates to it. Otherwise it
    performs a deterministic local mock run.
    """

    stage = "3.2.2"
    name = "runtime_adapter_dry_run"

    def __init__(self, adapter: Optional[Any] = None) -> None:
        self.adapter = adapter

    def run(
        self,
        chunks: Iterable[Mapping[str, Any]],
        handler: Optional[ChunkHandler] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> RuntimeAdapterDryRunResult:
        chunk_list = [dict(chunk) for chunk in chunks]
        safe_metadata = dict(metadata or {})

        if self.adapter is not None and hasattr(self.adapter, "run_with_scheduler"):
            delegated = self.adapter.run_with_scheduler(
                chunk_list,
                TranslationScheduler(),
                self._job_handler(handler or self._default_handler),
                metadata=safe_metadata,
            )
            return self._normalize_delegated_result(delegated, safe_metadata)

        if self.adapter is not None and hasattr(self.adapter, "run_with_handler"):
            delegated = self.adapter.run_with_handler(chunk_list, self._job_handler(handler or self._default_handler))
            return self._normalize_delegated_result(delegated, safe_metadata)

        return self._fallback_run(chunk_list, handler or self._default_handler, safe_metadata)

    def _fallback_run(
        self,
        chunks: List[Dict[str, Any]],
        handler: ChunkHandler,
        metadata: Dict[str, Any],
    ) -> RuntimeAdapterDryRunResult:
        chunk_results: List[Dict[str, Any]] = []
        failed_chunks: List[Dict[str, Any]] = []

        for position, chunk in enumerate(chunks, start=1):
            chunk_index = int(chunk.get("chunk_index", position))
            job_id = str(chunk.get("job_id", f"runtime-adapter-job-{chunk_index:06d}"))

            try:
                handled = handler(chunk)
                text = self._extract_text(handled)
                chunk_results.append(
                    {
                        "chunk_index": chunk_index,
                        "job_id": job_id,
                        "text": text,
                        "metadata": {
                            "stage": self.stage,
                            "dry_run": True,
                            **dict(chunk.get("metadata", {})),
                        },
                    }
                )
            except Exception as exc:  # pragma: no cover - exercised by failure tests
                failed_chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "job_id": job_id,
                        "error": type(exc).__name__,
                        "message": str(exc),
                        "metadata": {"stage": self.stage, "dry_run": True},
                    }
                )

        done = len(chunk_results)
        failed = len(failed_chunks)
        total = len(chunks)
        merge_ready = total > 0 and failed == 0 and done == total

        manifest = {
            "chunks_total": total,
            "chunks_done": done,
            "chunks_failed": failed,
            "merge_ready": merge_ready,
        }
        scheduler_summary = {
            "jobs_total": total,
            "done": done,
            "failed": failed,
            "merge_ready": merge_ready,
        }
        collector_manifest = {
            "chunks_total": total,
            "done_chunks": [item["chunk_index"] for item in chunk_results],
            "failed_chunks": [item["chunk_index"] for item in failed_chunks],
            "merge_ready": merge_ready,
        }
        export_outputs = {
            "merged_text": "\n".join(item["text"] for item in chunk_results),
            "chunk_results": chunk_results,
            "failed_chunks": failed_chunks,
            "manifest": manifest,
        }

        return RuntimeAdapterDryRunResult(
            scheduler_summary=scheduler_summary,
            collector_manifest=collector_manifest,
            failed_chunk_report=failed_chunks,
            dashboard_report={"scheduler": scheduler_summary},
            outputs_count=done,
            merge_ready=merge_ready,
            export_outputs=export_outputs,
            metadata={
                "stage": "TE-v3.2-stage-3.2.2",
                "adapter": self.adapter.__class__.__name__ if self.adapter else None,
                "provider_runtime": "not_connected",
                "http_api": "not_called",
                "api_key": "not_used",
                "launcher_flow": "not_modified",
                **metadata,
            },
        )

    def _normalize_delegated_result(
        self,
        delegated: Any,
        metadata: Dict[str, Any],
    ) -> RuntimeAdapterDryRunResult:
        if isinstance(delegated, RuntimeAdapterDryRunResult):
            return delegated

        if not isinstance(delegated, Mapping):
            raise TypeError("delegated dry-run result must be a mapping or RuntimeAdapterDryRunResult")

        export_outputs = dict(delegated.get("export_outputs") or delegated.get("outputs") or {})
        scheduler_summary = dict(delegated.get("scheduler_summary") or {})
        collector_manifest = dict(delegated.get("collector_manifest") or {})
        failed_chunk_report = list(delegated.get("failed_chunk_report") or export_outputs.get("failed_chunks") or [])
        dashboard_report = dict(delegated.get("dashboard_report") or {"scheduler": scheduler_summary})

        outputs_count = int(delegated.get("outputs_count", len(export_outputs.get("chunk_results", []))))
        merge_ready = bool(delegated.get("merge_ready", export_outputs.get("manifest", {}).get("merge_ready", False)))

        return RuntimeAdapterDryRunResult(
            scheduler_summary=scheduler_summary,
            collector_manifest=collector_manifest,
            failed_chunk_report=failed_chunk_report,
            dashboard_report=dashboard_report,
            outputs_count=outputs_count,
            merge_ready=merge_ready,
            export_outputs=export_outputs,
            metadata={
                "stage": "TE-v3.2-stage-3.2.2",
                "delegated": True,
                "provider_runtime": "not_connected",
                "http_api": "not_called",
                "api_key": "not_used",
                "launcher_flow": "not_modified",
                **metadata,
            },
        )

    @staticmethod
    def _default_handler(chunk: Mapping[str, Any]) -> str:
        return str(chunk.get("text", ""))

    @staticmethod
    def _job_handler(handler: ChunkHandler) -> Callable[[Any], Any]:
        def wrapped(job: Any) -> Any:
            chunk = job.package if isinstance(getattr(job, "package", None), Mapping) else {
                "chunk_index": getattr(job, "chunk_index", 1),
                "text": getattr(job, "source_text", ""),
                "metadata": getattr(job, "metadata", {}),
            }
            return handler(chunk)

        return wrapped

    @staticmethod
    def _extract_text(value: Any) -> str:
        if isinstance(value, Mapping):
            return str(value.get("text", ""))
        return str(value)


__all__ = ["RuntimeAdapterDryRun", "RuntimeAdapterDryRunResult"]
