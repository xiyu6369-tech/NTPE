# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from .export_context import ExportContext


class ExportWorkflowBridge:
    def __init__(self, export_engine: object) -> None:
        self.export_engine = export_engine

    def export_workflow_result(self, workflow_result: object, export_format: str = "txt", **kwargs):
        content = getattr(workflow_result, "content", None) or getattr(workflow_result, "output", None) or str(workflow_result)
        return self.export_engine.export(ExportContext(content=content, format=export_format, **kwargs))
