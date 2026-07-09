from __future__ import annotations

from core.translation_scheduler import JobStatus, TranslationScheduler, is_retryable_error


def test_retryable_error_catalog() -> None:
    assert is_retryable_error("provider timeout")
    assert is_retryable_error("503 service unavailable")
    assert is_retryable_error("ResourceExhausted")
    assert is_retryable_error("provider temporary failure")
    assert is_retryable_error("connection reset by peer")
    assert not is_retryable_error("empty source")
    assert not is_retryable_error("invalid package")
    assert not is_retryable_error("API key missing")
    assert not is_retryable_error("authentication failed")
    assert not is_retryable_error("permission denied")
    assert not is_retryable_error("schema error")


def test_timeout_retries_once_then_succeeds_and_preserves_merge_order() -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    scheduler.create_jobs(["chunk 1", "chunk 2", "chunk 3"])
    calls: dict[int, int] = {}

    def handler(job):
        calls[job.chunk_index] = calls.get(job.chunk_index, 0) + 1
        if job.chunk_index == 2 and calls[job.chunk_index] == 1:
            raise TimeoutError("provider timeout")
        return f"translated {job.chunk_index}"

    scheduler.run(handler)
    summary = scheduler.summary()

    assert scheduler.collector.merge_results() == "translated 1\ntranslated 2\ntranslated 3"
    assert summary["done"] == 3
    assert summary["failed"] == 0
    assert summary["retry"] == 0
    assert summary["retry_attempts_total"] == 1
    assert summary["retryable_failures"] == 1
    assert calls[2] == 2


def test_non_retryable_error_fails_without_retry() -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    scheduler.create_jobs(["chunk 1", "chunk 2"])

    def handler(job):
        if job.chunk_index == 2:
            raise RuntimeError("authentication failed")
        return f"translated {job.chunk_index}"

    scheduler.run(handler)
    jobs = scheduler.queue.all_jobs()
    summary = scheduler.summary()

    assert jobs[1].status == JobStatus.FAILED
    assert jobs[1].retry_count == 0
    assert scheduler.collector.merge_results() == "translated 1"
    assert summary["non_retryable_failures"] == 1
    assert summary["retry_attempts_total"] == 0


def test_retryable_error_fails_after_max_attempts() -> None:
    scheduler = TranslationScheduler(default_max_attempts=2)
    scheduler.create_jobs(["chunk 1"])

    def handler(job):
        raise TimeoutError("provider timeout")

    scheduler.run(handler)
    job = scheduler.queue.all_jobs()[0]
    summary = scheduler.summary()

    assert job.status == JobStatus.FAILED
    assert job.attempts == 2
    assert job.retry_count == 1
    assert summary["failed"] == 1
    assert summary["max_attempt_failures"] == 1
    assert summary["retry_attempts_total"] == 1


def main() -> int:
    test_retryable_error_catalog()
    test_timeout_retries_once_then_succeeds_and_preserves_merge_order()
    test_non_retryable_error_fails_without_retry()
    test_retryable_error_fails_after_max_attempts()
    print("NTPE TE-v3.1 Stage-3.1.2 Retry Queue PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
