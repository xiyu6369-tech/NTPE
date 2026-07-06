from core.workflow.export_context import ExportContext
from core.workflow.export_engine import ExportEngine
from core.workflow.export_metadata import ExportMetadata
from core.workflow.export_metrics import build_export_metrics
from core.workflow.export_pipeline import ExportPipeline


def test_export_engine_txt_and_markdown():
    engine = ExportEngine()
    txt = engine.export(ExportContext(content="第一段", format="txt"))
    md = engine.export(ExportContext(content="第二段", format="markdown", metadata=ExportMetadata(title="章節")))
    assert txt.success is True
    assert txt.content == "第一段"
    assert md.success is True
    assert md.content.startswith("# 章節")


def test_export_pipeline_many_formats():
    engine = ExportEngine()
    pipeline = ExportPipeline(engine)
    results = pipeline.export_many("內容", ["txt", "html"])
    metrics = build_export_metrics(results)
    assert metrics["success"] == 2
    assert metrics["formats"] == ["html", "txt"]


def test_unknown_export_format_fails_cleanly():
    engine = ExportEngine()
    result = engine.export(ExportContext(content="內容", format="unknown"))
    assert result.success is False
    assert "exporter_not_found" in result.error
