# =====================================================
# NTPE 1.2 Professional
# Stage-15.6 Quality Report / Export Layer Tests
# =====================================================

from __future__ import annotations

import json

from core.quality import QualityContext, QualityReportExporter, QualityResult, QualityIssue, QualitySeverity


def test_quality_exporter_writes_clean_files(tmp_path):
    context = QualityContext(
        source_text="안녕하세요",
        translated_text="你好",
        segment_id="seg-001",
        session_id="session-001",
        provider_name="nvidia",
        model_name="test-model",
        metadata={"api_key": "sk-secret-value", "safe": "ok"},
    )
    result = QualityResult(metrics={"source_length": 5, "translated_length": 2})
    result.add_issue(
        QualityIssue(
            rule_name="sample_rule",
            category="formatting",
            severity=QualitySeverity.WARNING,
            message="sample issue",
            score_penalty=2.0,
            metadata={"line": 1},
        )
    )

    bundle = QualityReportExporter(tmp_path).export(context, result)

    assert set(bundle.files) == {"json", "summary", "metrics", "issues_csv"}
    for path in bundle.files.values():
        assert path.exists()
        assert path.name.startswith("seg-001")

    payload = json.loads(bundle.files["json"].read_text(encoding="utf-8"))
    assert payload["stage"] == "Stage-15.6"
    assert payload["context"]["metadata"]["api_key"] != "sk-secret-value"
    assert payload["context"]["metadata"]["safe"] == "ok"
    assert payload["summary"]["issue_count"] == 1


def test_quality_exporter_supports_selected_formats(tmp_path):
    context = QualityContext(source_text="a", translated_text="b", segment_id="seg/unsafe")
    result = QualityResult()

    bundle = QualityReportExporter(tmp_path).export(context, result, formats=("json",))

    assert list(bundle.files) == ["json"]
    assert bundle.files["json"].name == "seg_unsafe.quality.json"
