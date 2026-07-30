# =====================================================
# NTPE 1.2 Professional
# Stage-17.2 Job Scheduler / Batch Task Manager Launcher Test
# =====================================================

from core.workflow import JobPriority, JobQueue, JobScheduler


def main() -> int:
    scheduler = JobScheduler()
    low = scheduler.submit("低優先任務", priority=JobPriority.LOW)
    high = scheduler.submit("高優先任務", priority=JobPriority.HIGH)
    first = scheduler.run_next()
    scheduler.submit("一般任務", priority="normal")
    results = scheduler.run_all()
    metrics = scheduler.metrics()
    queue = JobQueue()
    queue.put("A", priority="low")
    queue.put("B", priority="critical")
    priority_ok = queue.get().source_text == "B"
    checks = [
        ("Scheduler Created", scheduler.name.endswith("Batch Task Manager")),
        ("Priority Scheduling", first.job_id == high.job_id and low.job_id != high.job_id),
        ("Batch Completed", first.success and all(result.success for result in results)),
        ("Metrics Completed", metrics.get("completed_jobs") == 3),
        ("Queue Priority", priority_ok),
    ]
    print("NTPE 1.2 Professional - Stage-17.2 Job Scheduler")
    print("=" * 68)
    failed = False
    for name, ok in checks:
        print(f"{name:28} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
