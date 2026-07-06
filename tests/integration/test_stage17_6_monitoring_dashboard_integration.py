from core.workflow import ExportEngine, MonitoringDashboardAPI, TranslationWorkflowEngine
from core.workflow.dashboard_status import normalize_status


def test_dashboard_integrates_workflow_and_export_layers():
    workflow = TranslationWorkflowEngine().execute("hello")
    export_engine = ExportEngine()
    api = MonitoringDashboardAPI()
    api.register_source("workflow", lambda: normalize_status("workflow", workflow))
    api.register_source("export_framework", lambda: normalize_status("export_framework", {"status": "ready", "metrics": {"exports": len(export_engine.results)}}))
    snapshot = api.snapshot()
    assert snapshot.status == "ok"
    assert {item.component for item in snapshot.components} == {"workflow", "export_framework"}
