from core.workflow import TranslationWorkflowEngine


def test_stage17_1_workflow_integration_contract():
    engine = TranslationWorkflowEngine()
    result = engine.execute("鄭泰義走進房間。")
    assert result.success
    assert result.metrics["has_translation"] is True
    assert result.metrics["has_quality_report"] is True
    assert result.metrics["has_export"] is True
