from core.workflow import JobPriority, JobQueue, JobScheduler


def test_job_scheduler_runs_batch():
    scheduler = JobScheduler()
    scheduler.submit_many(["一", "二"])
    results = scheduler.run_all()
    assert len(results) == 2
    assert all(result.success for result in results)
    assert scheduler.metrics()["completed_jobs"] == 2


def test_job_queue_priority_order():
    queue = JobQueue()
    queue.put("low", priority=JobPriority.LOW)
    queue.put("critical", priority=JobPriority.CRITICAL)
    assert queue.get().source_text == "critical"


def test_scheduler_pause_resume():
    scheduler = JobScheduler()
    scheduler.submit("text")
    scheduler.pause()
    assert scheduler.queue.paused is True
    scheduler.resume()
    assert scheduler.run_next().success is True
