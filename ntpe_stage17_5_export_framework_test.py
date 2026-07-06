from core.workflow.export_context import ExportContext
from core.workflow.export_engine import ExportEngine
from core.workflow.export_metadata import ExportMetadata
from core.workflow.export_metrics import build_export_metrics
from core.workflow.export_pipeline import ExportPipeline


def main() -> int:
    engine = ExportEngine()
    context = ExportContext(content="第一章\n這是一段譯文。", format="markdown", metadata=ExportMetadata(title="測試章節"))
    result = engine.export(context)
    assert result.success is True
    assert result.content.startswith("# 測試章節")

    pipeline = ExportPipeline(engine)
    results = pipeline.export_many("完成內容", ["txt", "html"])
    metrics = build_export_metrics(results)
    assert metrics["success"] == 2
    assert "txt" in metrics["formats"]
    assert "html" in metrics["formats"]
    print("Stage-17.5 Export Framework PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
