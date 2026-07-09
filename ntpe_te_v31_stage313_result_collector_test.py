from __future__ import annotations

from core.translation_scheduler import JobStatus, TranslationCollector, TranslationJob


def _done(job_id: str, chunk_index: int, result: str) -> TranslationJob:
    job = TranslationJob(job_id=job_id, chunk_index=chunk_index, source_text=f"source {chunk_index}")
    job.status = JobStatus.DONE
    job.result = result
    job.attempts = 1
    return job


def _failed(job_id: str, chunk_index: int, error: str) -> TranslationJob:
    job = TranslationJob(job_id=job_id, chunk_index=chunk_index, source_text=f"source {chunk_index}")
    job.status = JobStatus.FAILED
    job.error = error
    job.last_error = error
    job.attempts = 2
    job.retry_count = 1
    job.error_history = ["provider timeout", error]
    return job


def test_collector_merges_out_of_order_results_by_chunk_index() -> None:
    collector = TranslationCollector(chunks_total=3)
    collector.collect(_done("job-3", 3, "translated 3"))
    collector.collect(_done("job-1", 1, "translated 1"))
    collector.collect(_done("job-2", 2, "translated 2"))

    assert collector.merge_results() == "translated 1\ntranslated 2\ntranslated 3"
    assert collector.collected_count() == 3


def test_failed_chunk_placeholder_and_report_do_not_pollute_default_merge() -> None:
    collector = TranslationCollector(chunks_total=3)
    collector.collect(_done("job-1", 1, "translated 1"))
    collector.collect_failure(_failed("job-2", 2, "timeout"))
    collector.collect(_done("job-3", 3, "translated 3"))
    report = collector.build_failed_chunk_report()

    assert collector.merge_results() == "translated 1\ntranslated 3"
    assert collector.merge_results(include_failed=True) == "translated 1\n[FAILED chunk 0002: timeout]\ntranslated 3"
    assert report == [
        {
            "chunk_index": 2,
            "job_id": "job-2",
            "error": "timeout",
            "attempts": 2,
            "retry_count": 1,
            "error_history": ["provider timeout", "timeout"],
            "status": "FAILED",
        }
    ]


def test_duplicate_collection_keeps_first_result_and_records_conflict() -> None:
    collector = TranslationCollector(chunks_total=2)
    collector.collect(_done("job-1", 1, "translated 1"))
    collector.collect(_done("job-1-repeat", 1, "translated 1"))
    collector.collect(_done("job-1-conflict", 1, "translated changed"))
    collector.collect(_done("job-2", 2, "translated 2"))
    manifest = collector.build_manifest()

    assert collector.merge_results() == "translated 1\ntranslated 2"
    assert collector.duplicate_count() == 2
    assert collector.conflict_count() == 1
    assert manifest["duplicates"][0]["conflict"] is False
    assert manifest["duplicates"][1]["conflict"] is True
    assert manifest["conflicts"] == [1]


def test_manifest_statistics_are_correct() -> None:
    collector = TranslationCollector(chunks_total=4)
    collector.collect(_done("job-1", 1, "translated 1"))
    collector.collect_failure(_failed("job-3", 3, "timeout"))
    manifest = collector.build_manifest()

    assert manifest["chunks_total"] == 4
    assert manifest["chunks_done"] == 1
    assert manifest["chunks_failed"] == 1
    assert manifest["chunks_missing"] == 2
    assert manifest["chunk_order"] == [1, 2, 3, 4]
    assert manifest["done_chunks"] == [1]
    assert manifest["failed_chunks"] == [3]
    assert manifest["missing_chunks"] == [2, 4]
    assert manifest["merge_ready"] is False


def main() -> int:
    test_collector_merges_out_of_order_results_by_chunk_index()
    test_failed_chunk_placeholder_and_report_do_not_pollute_default_merge()
    test_duplicate_collection_keeps_first_result_and_records_conflict()
    test_manifest_statistics_are_correct()
    print("NTPE TE-v3.1 Stage-3.1.3 Result Collector PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
