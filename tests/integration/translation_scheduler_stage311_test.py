from __future__ import annotations

from core.translation_scheduler import TranslationCollector, TranslationJob, TranslationQueue


def test_collector_preserves_chunk_order_when_jobs_complete_out_of_order() -> None:
    collector = TranslationCollector()
    job_1 = TranslationJob(job_id="job-1", chunk_index=1, source_text="source 1")
    job_2 = TranslationJob(job_id="job-2", chunk_index=2, source_text="source 2")
    job_3 = TranslationJob(job_id="job-3", chunk_index=3, source_text="source 3")

    queue = TranslationQueue()
    for job in (job_1, job_2, job_3):
        queue.enqueue(job)

    queue.mark_done("job-2", "translated 2")
    collector.collect(job_2)
    queue.mark_done("job-1", "translated 1")
    collector.collect(job_1)
    queue.mark_done("job-3", "translated 3")
    collector.collect(job_3)

    assert collector.get_result(1) == "translated 1"
    assert collector.get_result(2) == "translated 2"
    assert collector.get_result(3) == "translated 3"
    assert collector.merge_results() == "translated 1\ntranslated 2\ntranslated 3"


def test_failed_job_does_not_pollute_successful_merge() -> None:
    collector = TranslationCollector()
    queue = TranslationQueue()
    jobs = [
        TranslationJob(job_id="job-1", chunk_index=1, source_text="source 1"),
        TranslationJob(job_id="job-2", chunk_index=2, source_text="source 2"),
        TranslationJob(job_id="job-3", chunk_index=3, source_text="source 3"),
    ]
    for job in jobs:
        queue.enqueue(job)

    queue.mark_done("job-1", "translated 1")
    queue.mark_failed("job-2", "mock provider timeout")
    queue.mark_done("job-3", "translated 3")

    assert collector.collect(jobs[0]) is True
    assert collector.collect(jobs[1]) is False
    assert collector.collect(jobs[2]) is True
    assert collector.merge_results() == "translated 1\ntranslated 3"
    assert queue.done_count() == 2
    assert queue.failed_count() == 1
