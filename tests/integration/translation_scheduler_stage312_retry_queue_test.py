from __future__ import annotations

from core.translation_scheduler import JobStatus, TranslationScheduler


def test_mixed_retry_queue_outcomes_keep_successful_merge_clean() -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    scheduler.create_jobs(["job1", "job2", "job3", "job4", "job5"])
    calls: dict[int, int] = {}

    def handler(job):
        calls[job.chunk_index] = calls.get(job.chunk_index, 0) + 1
        if job.chunk_index == 2 and calls[job.chunk_index] == 1:
            raise TimeoutError("provider timeout")
        if job.chunk_index == 3 and calls[job.chunk_index] == 1:
            raise RuntimeError("503 service unavailable")
        if job.chunk_index == 4:
            raise RuntimeError("authentication failed")
        if job.chunk_index == 5:
            raise TimeoutError("provider timeout")
        return f"translated {job.chunk_index}"

    processed = scheduler.run(handler)
    jobs = scheduler.queue.all_jobs()
    summary = scheduler.summary()

    assert len(processed) == 8
    assert [job.status for job in jobs] == [
        JobStatus.DONE,
        JobStatus.DONE,
        JobStatus.DONE,
        JobStatus.FAILED,
        JobStatus.FAILED,
    ]
    assert scheduler.collector.merge_results() == "translated 1\ntranslated 2\ntranslated 3"
    assert jobs[3].retry_count == 0
    assert jobs[4].retry_count == 1
    assert summary["jobs_total"] == 5
    assert summary["pending"] == 0
    assert summary["running"] == 0
    assert summary["done"] == 3
    assert summary["failed"] == 2
    assert summary["retry"] == 0
    assert summary["retry_attempts_total"] == 3
    assert summary["retryable_failures"] == 3
    assert summary["non_retryable_failures"] == 1
    assert summary["max_attempt_failures"] == 1


def test_done_job_cannot_be_marked_for_retry_or_collected_twice() -> None:
    scheduler = TranslationScheduler()
    jobs = scheduler.create_jobs(["job1"])
    scheduler.run(lambda job: "translated 1")

    assert scheduler.collector.collect(jobs[0]) is False
    try:
        scheduler.queue.mark_retry(jobs[0].job_id, "provider timeout")
    except ValueError:
        retry_blocked = True
    else:
        retry_blocked = False

    assert retry_blocked is True
    assert jobs[0].status == JobStatus.DONE
    assert scheduler.collector.merge_results() == "translated 1"
