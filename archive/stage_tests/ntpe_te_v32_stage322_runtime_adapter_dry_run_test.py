from core.translation_scheduler.runtime_adapter_dry_run import RuntimeAdapterDryRun
from core.translation_scheduler.runtime_adapter import RuntimeSchedulerAdapter


def check(name, condition):
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v3.2 Stage-3.2.2 Runtime Adapter Dry Run Test")
    print("=" * 72)

    adapter = RuntimeSchedulerAdapter()
    dry_run = RuntimeAdapterDryRun(adapter=adapter)

    chunks = [
        {"chunk_index": 1, "text": "T1", "metadata": {"source": "dry-run"}},
        {"chunk_index": 2, "text": "T2", "metadata": {"source": "dry-run"}},
    ]

    result = dry_run.run(
        chunks,
        handler=lambda chunk: {"text": chunk["text"]},
        metadata={"profile": "literary"},
    )

    check("Dry Run Created", result is not None)
    check("Jobs Total", result.scheduler_summary["jobs_total"] == 2)
    check("Jobs Done", result.scheduler_summary["done"] == 2)
    check("Jobs Failed", result.scheduler_summary["failed"] == 0)
    check("Collector Total", result.collector_manifest["chunks_total"] == 2)
    check("Collector Done", result.collector_manifest["done_chunks"] == [1, 2])
    check("No Failed Chunks", result.failed_chunk_report == [])
    check("Outputs Count", result.outputs_count == 2)
    check("Merge Ready", result.merge_ready is True)
    check("Merged Text", result.export_outputs["merged_text"] == "T1\nT2")
    check("Chunk Result Count", len(result.export_outputs["chunk_results"]) == 2)
    check("Manifest Done", result.export_outputs["manifest"]["chunks_done"] == 2)
    check("Provider Not Connected", result.metadata["provider_runtime"] == "not_connected")
    check("HTTP Not Called", result.metadata["http_api"] == "not_called")
    check("API Key Not Used", result.metadata["api_key"] == "not_used")
    check("Launcher Not Modified", result.metadata["launcher_flow"] == "not_modified")

    failure = dry_run.run(
        chunks,
        handler=lambda chunk: (_ for _ in ()).throw(RuntimeError("mock failure"))
        if chunk["chunk_index"] == 2
        else {"text": chunk["text"]},
    )

    check("Failure Jobs Total", failure.scheduler_summary["jobs_total"] == 2)
    check("Failure Jobs Done", failure.scheduler_summary["done"] == 1)
    check("Failure Jobs Failed", failure.scheduler_summary["failed"] == 1)
    check("Failure Merge Blocked", failure.merge_ready is False)
    check("Failure Report", failure.failed_chunk_report[0]["chunk_index"] == 2)

    print("NTPE TE-v3.2 Stage-3.2.2 Runtime Adapter Dry Run PASS")


if __name__ == "__main__":
    main()
