from __future__ import annotations

import os
import sys

from core.translation_scheduler import JobStatus, RuntimeSchedulerAdapter


def test_runtime_scheduler_adapter_mock_flow_without_provider_runtime() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    before_provider_runtime = "core.translation_engine.provider_runtime" in sys.modules
    try:
        adapter = RuntimeSchedulerAdapter()
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        packages = [{"profile": "mock-a"}, {"profile": "mock-b"}, {"profile": "mock-c"}]
        metadata = {"runtime_source": "stage-3.2.1", "stage": "TE-v3.2", "profile": "mock"}
        scheduler = adapter.create_scheduler_from_chunks(chunks, packages=packages, metadata=metadata)

        jobs = scheduler.queue.all_jobs()
        assert [job.chunk_index for job in jobs] == [1, 2, 3]
        assert [job.source_text for job in jobs] == chunks
        assert jobs[0].package == packages[0]
        assert jobs[0].metadata["runtime_source"] == "stage-3.2.1"

        scheduler = adapter.run_with_handler(
            chunks,
            lambda job: {"text": f"translated text {job.chunk_index}", "metadata": {"mock": True}},
            packages=packages,
        )

        assert [job.status for job in scheduler.queue.all_jobs()] == [JobStatus.DONE, JobStatus.DONE, JobStatus.DONE]
        assert scheduler.collector.merge_results() == "translated text 1\ntranslated text 2\ntranslated text 3"
        assert scheduler.queue.all_jobs()[0].result == "translated text 1"
        assert scheduler.queue.all_jobs()[0].result_metadata == {"mock": True}

        report = adapter.build_runtime_report(scheduler)
        outputs = adapter.export_outputs(scheduler)

        assert report["scheduler_summary"]["done"] == 3
        assert report["collector_manifest"]["chunks_done"] == 3
        assert report["failed_chunk_report"] == []
        assert report["dashboard_report"]["scheduler"]["jobs_total"] == 3
        assert report["outputs_count"] == 3
        assert report["merge_ready"] is True
        assert outputs["merged_text"] == "translated text 1\ntranslated text 2\ntranslated text 3"
        assert [item["text"] for item in outputs["chunk_results"]] == [
            "translated text 1",
            "translated text 2",
            "translated text 3",
        ]
        assert outputs["failed_chunks"] == []
        assert outputs["manifest"]["merge_ready"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules or before_provider_runtime
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_scheduler_adapter_mock_flow_without_provider_runtime()
    print("NTPE TE-v3.2 Stage-3.2.1 Runtime Scheduler Adapter PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
