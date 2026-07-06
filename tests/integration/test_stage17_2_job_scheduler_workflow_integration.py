from core.workflow import JobScheduler, TranslationWorkflowEngine


def test_job_scheduler_binds_workflow_engine():
    scheduler = JobScheduler(TranslationWorkflowEngine())
    scheduler.submit("第一段。\n第二段。")
    result = scheduler.run_next()
    assert result.success
    assert result.artifacts["translation"].startswith("第一段")
    assert "quality_report" in result.artifacts
