from __future__ import annotations

from core.translation_scheduler import JobStatus, TranslationJob, TranslationScheduler


def test_mixed_result_collector_manifest_and_scheduler_summary() -> None:
    scheduler = TranslationScheduler()
    jobs = scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3", "chunk 4", "chunk 5"])

    scheduler.queue.mark_done(jobs[0].job_id, "translated 1")
    scheduler.collector.collect(jobs[0])

    scheduler.queue.mark_failed(jobs[1].job_id, "timeout")
    scheduler.collector.collect_failure(jobs[1])

    scheduler.queue.mark_done(jobs[2].job_id, "translated 3")
    scheduler.collector.collect(jobs[2])

    scheduler.queue.mark_done(jobs[3].job_id, "translated 4")
    scheduler.collector.collect(jobs[3])

    duplicate = TranslationJob(job_id="job-4-duplicate", chunk_index=4, source_text="chunk 4")
    duplicate.status = JobStatus.DONE
    duplicate.result = "translated 4 changed"
    scheduler.collector.collect(duplicate)

    manifest = scheduler.collector.build_manifest()
    summary = scheduler.summary()

    assert scheduler.collector.merge_results() == "translated 1\ntranslated 3\ntranslated 4"
    assert scheduler.collector.merge_results(include_failed=True) == "translated 1\n[FAILED chunk 0002: timeout]\ntranslated 3\ntranslated 4"
    assert manifest["chunks_total"] == 5
    assert manifest["done_chunks"] == [1, 3, 4]
    assert manifest["failed_chunks"] == [2]
    assert manifest["missing_chunks"] == [5]
    assert manifest["chunks_missing"] == 1
    assert manifest["duplicates"][0]["chunk_index"] == 4
    assert manifest["duplicates"][0]["conflict"] is True
    assert manifest["conflicts"] == [4]
    assert manifest["merge_ready"] is False
    assert summary["collected"] == 3
    assert summary["collector_failed"] == 1
    assert summary["duplicates"] == 1
    assert summary["conflicts"] == 1
    assert summary["merge_ready"] is False


def test_failed_chunk_report_keeps_retry_metadata() -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    scheduler.create_jobs(["chunk 1"])

    def handler(job):
        raise TimeoutError("provider timeout")

    scheduler.run(handler)
    report = scheduler.collector.build_failed_chunk_report()

    assert report[0]["chunk_index"] == 1
    assert report[0]["job_id"] == "translation-job-000001"
    assert report[0]["error"] == "provider timeout"
    assert report[0]["attempts"] == 2
    assert report[0]["retry_count"] == 1
    assert report[0]["error_history"] == ["provider timeout", "provider timeout"]
    assert report[0]["status"] == "FAILED"
