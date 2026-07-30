from __future__ import annotations

from core.translation_scheduler import JobStatus, TranslationScheduler


def test_scheduler_creates_three_jobs() -> None:
    scheduler = TranslationScheduler()
    jobs = scheduler.create_jobs(["chunk one", "chunk two", "chunk three"])

    assert len(jobs) == 3
    assert [job.chunk_index for job in jobs] == [1, 2, 3]
    assert all(job.status == JobStatus.PENDING for job in jobs)
    assert scheduler.summary()["jobs_total"] == 3
    assert scheduler.summary()["pending"] == 3


def test_dispatch_marks_all_jobs_done_and_merges_in_order() -> None:
    scheduler = TranslationScheduler()
    scheduler.create_jobs(["alpha", "beta", "gamma"])

    completed = scheduler.run(lambda job: f"translated-{job.chunk_index}")
    summary = scheduler.summary()

    assert len(completed) == 3
    assert all(job.status == JobStatus.DONE for job in completed)
    assert scheduler.collector.merge_results() == "translated-1\ntranslated-2\ntranslated-3"
    assert summary["jobs_total"] == 3
    assert summary["pending"] == 0
    assert summary["running"] == 0
    assert summary["done"] == 3
    assert summary["failed"] == 0
    assert summary["retry"] == 0
    assert summary["elapsed_seconds"] >= 0


def main() -> int:
    test_scheduler_creates_three_jobs()
    test_dispatch_marks_all_jobs_done_and_merges_in_order()
    print("NTPE TE-v3.1 Stage-3.1.1 Translation Scheduler Skeleton PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
