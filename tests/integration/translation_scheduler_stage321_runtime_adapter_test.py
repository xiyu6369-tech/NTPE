from __future__ import annotations

import sys
from pathlib import Path

from core.translation_scheduler import JobStatus, RuntimeSchedulerAdapter


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_adapter_mixed_retry_failure_flow_without_provider_or_launcher() -> None:
    launcher_before = (ROOT / "launcher_translate.py").read_text(encoding="utf-8")
    adapter = RuntimeSchedulerAdapter(default_max_attempts=2)
    chunks = ["chunk 1", "chunk 2", "chunk 3"]
    calls: dict[int, int] = {}

    def handler(job):
        calls[job.chunk_index] = calls.get(job.chunk_index, 0) + 1
        if job.chunk_index == 2 and calls[job.chunk_index] == 1:
            raise TimeoutError("provider timeout")
        if job.chunk_index == 3:
            raise RuntimeError("schema error")
        return {"text": f"adapter translated {job.chunk_index}", "metadata": {"attempt": calls[job.chunk_index]}}

    scheduler = adapter.run_with_handler(chunks, handler)
    jobs = scheduler.queue.all_jobs()
    report = adapter.build_runtime_report(scheduler)
    outputs = adapter.export_outputs(scheduler)

    assert [job.status for job in jobs] == [JobStatus.DONE, JobStatus.DONE, JobStatus.FAILED]
    assert calls == {1: 1, 2: 2, 3: 1}
    assert scheduler.collector.merge_results() == "adapter translated 1\nadapter translated 2"
    assert jobs[1].retry_count == 1
    assert jobs[2].retry_count == 0
    assert outputs["merged_text"] == "adapter translated 1\nadapter translated 2"
    assert [item["chunk_index"] for item in outputs["chunk_results"]] == [1, 2]
    assert outputs["failed_chunks"][0]["chunk_index"] == 3
    assert outputs["failed_chunks"][0]["error"] == "schema error"
    assert report["dashboard_report"]["scheduler"]["jobs_total"] == 3
    assert report["dashboard_report"]["queue"]["failed_count"] == 1
    assert report["collector_manifest"]["failed_chunks"] == [3]
    assert report["merge_ready"] is True
    assert "core.translation_engine.provider_runtime" not in sys.modules
    assert "core.production_runtime" not in sys.modules
    assert "requests" not in sys.modules
    assert "httpx" not in sys.modules
    assert (ROOT / "launcher_translate.py").read_text(encoding="utf-8") == launcher_before
