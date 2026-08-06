"""Regression test suite for Quality Feedback Loop (RM-5.9.2).

Tests models, rules, generator, serializer, and CLI --feedback integration.
All tests are offline and deterministic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from core.knowledge_benchmark.feedback.models import (
    FeedbackSeverity,
    FeedbackRuleStatus,
    QualityFeedbackItem,
    QualityFeedbackReport,
)
from core.knowledge_benchmark.feedback.rules import (
    FeedbackRule,
    BUILTIN_FEEDBACK_RULES,
    create_builtin_rules,
)
from core.knowledge_benchmark.feedback.generator import (
    FeedbackReportGenerator,
    create_feedback_report_generator,
)
from core.knowledge_benchmark.feedback.serializer import (
    serialize_to_json,
    serialize_to_markdown,
    save_report,
)
from core.knowledge_benchmark.runtime.models import (
    QualityDecision,
    QualityStatus,
    QualityScorecard,
)


class TestFeedbackSeverity:
    def test_values(self):
        assert FeedbackSeverity.CRITICAL == "CRITICAL"
        assert FeedbackSeverity.HIGH == "HIGH"
        assert FeedbackSeverity.MEDIUM == "MEDIUM"
        assert FeedbackSeverity.LOW == "LOW"
        assert FeedbackSeverity.INFO == "INFO"


class TestFeedbackRuleStatus:
    def test_values(self):
        assert FeedbackRuleStatus.PASS == "PASS"
        assert FeedbackRuleStatus.FAIL == "FAIL"
        assert FeedbackRuleStatus.WARNING == "WARNING"
        assert FeedbackRuleStatus.SKIPPED == "SKIPPED"


class TestQualityFeedbackItem:
    def test_creation(self):
        item = QualityFeedbackItem(
            rule_id="FB-TEST-001",
            metric="f1",
            current_value=0.75,
            target_value=0.80,
            delta=-0.05,
            status=FeedbackRuleStatus.FAIL,
            severity=FeedbackSeverity.CRITICAL,
            description="F1 below threshold",
            recommendation="Improve F1 score",
        )
        assert item.rule_id == "FB-TEST-001"
        assert item.metric == "f1"
        assert item.current_value == 0.75
        assert item.status == FeedbackRuleStatus.FAIL

    def test_to_dict(self):
        item = QualityFeedbackItem(
            rule_id="FB-TEST-002",
            metric="precision",
            current_value=0.90,
            target_value=0.85,
            delta=0.0,
            status=FeedbackRuleStatus.PASS,
            severity=FeedbackSeverity.INFO,
        )
        d = item.to_dict()
        assert d["rule_id"] == "FB-TEST-002"
        assert d["status"] == "PASS"
        assert d["severity"] == "INFO"
        assert d["current_value"] == 0.90


class TestQualityFeedbackReport:
    def test_creation_empty(self):
        report = QualityFeedbackReport(report_id="test-001")
        assert report.report_id == "test-001"
        assert report.critical_count == 0
        assert report.fail_count == 0
        assert report.warning_count == 0
        assert report.pass_count == 0

    def test_to_dict(self):
        item = QualityFeedbackItem(
            rule_id="FB-F1-001",
            metric="f1",
            current_value=0.92,
            target_value=0.80,
            delta=0.0,
            status=FeedbackRuleStatus.PASS,
            severity=FeedbackSeverity.INFO,
        )
        report = QualityFeedbackReport(
            report_id="RPT-001",
            source_decision_status="PASS",
            overall_severity=FeedbackSeverity.INFO,
            items=[item],
            summary=["All clear"],
        )
        d = report.to_dict()
        assert d["report_id"] == "RPT-001"
        assert len(d["items"]) == 1
        assert d["summary"] == ["All clear"]

    def test_to_json(self):
        report = QualityFeedbackReport(
            report_id="JSON-001",
            source_decision_status="PASS",
            overall_severity=FeedbackSeverity.INFO,
        )
        js = report.to_json()
        parsed = json.loads(js)
        assert parsed["report_id"] == "JSON-001"

    def test_counters_with_items(self):
        items = [
            QualityFeedbackItem(rule_id="R1", metric="a", current_value=0.9, target_value=0.8, delta=0.0, status=FeedbackRuleStatus.PASS, severity=FeedbackSeverity.INFO),
            QualityFeedbackItem(rule_id="R2", metric="b", current_value=0.5, target_value=0.8, delta=-0.3, status=FeedbackRuleStatus.FAIL, severity=FeedbackSeverity.CRITICAL),
            QualityFeedbackItem(rule_id="R3", metric="c", current_value=0.7, target_value=0.8, delta=-0.1, status=FeedbackRuleStatus.WARNING, severity=FeedbackSeverity.MEDIUM),
        ]
        report = QualityFeedbackReport(report_id="CNT-001", items=items)
        assert report.pass_count == 1
        assert report.fail_count == 1
        assert report.warning_count == 1
        assert report.critical_count == 1


class TestFeedbackRule:
    def test_evaluate_pass(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-PASS",
            metric="test_metric",
            field_key="value",
            target_min=0.0,
            target_max=1.0,
        )
        item = rule.evaluate({"value": 0.85})
        assert item.status == FeedbackRuleStatus.PASS
        assert item.metric == "test_metric"

    def test_evaluate_fail(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-FAIL",
            metric="test_metric",
            field_key="value",
            target_min=0.70,
            target_max=0.90,
            severity_violation=FeedbackSeverity.CRITICAL,
        )
        item = rule.evaluate({"value": 0.50})
        assert item.status == FeedbackRuleStatus.FAIL
        assert item.severity == FeedbackSeverity.CRITICAL

    def test_evaluate_warning(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-WARN",
            metric="test_metric",
            field_key="value",
            target_min=0.70,
            target_max=0.90,
            severity_violation=FeedbackSeverity.MEDIUM,
        )
        item = rule.evaluate({"value": 0.50})
        assert item.status == FeedbackRuleStatus.WARNING
        assert item.severity == FeedbackSeverity.MEDIUM

    def test_evaluate_skipped(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-SKIP",
            metric="test_metric",
            field_key="nonexistent.path",
            target_min=0.0,
            target_max=1.0,
        )
        item = rule.evaluate({})
        assert item.status == FeedbackRuleStatus.SKIPPED

    def test_evaluate_nested_value(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-NESTED",
            metric="nested_metric",
            field_key="scorecard.f1",
            target_min=0.80,
            target_max=1.0,
        )
        scorecard_data: Dict[str, Any] = {"scorecard": {"f1": 0.92}}
        item = rule.evaluate(scorecard_data)
        assert item.status == FeedbackRuleStatus.PASS
        assert item.current_value == 0.92

    def test_evaluate_dict_value(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-DICTVAL",
            metric="dict_metric",
            field_key="scorecard.val",
            target_min=0.70,
            target_max=1.0,
        )
        scorecard_data: Dict[str, Any] = {"scorecard": {"val": {"value": 0.85}}}
        item = rule.evaluate(scorecard_data)
        assert item.status == FeedbackRuleStatus.PASS
        assert item.current_value == 0.85

    def test_evaluate_above_max(self):
        rule = FeedbackRule(
            rule_id="FB-TEST-ABOVE",
            metric="ece",
            field_key="ece",
            target_min=0.0,
            target_max=0.05,
            severity_violation=FeedbackSeverity.HIGH,
        )
        item = rule.evaluate({"ece": 0.15})
        assert item.status == FeedbackRuleStatus.FAIL
        assert item.delta == pytest.approx(-0.15, abs=0.01)


class TestBuiltinRules:
    def test_all_rules_present(self):
        rules = create_builtin_rules()
        assert len(rules) == 5
        rule_ids = {r.rule_id for r in rules}
        assert "FB-PRECISION-001" in rule_ids
        assert "FB-RECALL-001" in rule_ids
        assert "FB-F1-001" in rule_ids
        assert "FB-ECE-001" in rule_ids
        assert "FB-OVERALL-001" in rule_ids


class TestFeedbackReportGenerator:
    def _make_passing_decision(self) -> QualityDecision:
        return QualityDecision(
            status=QualityStatus.PASS,
            scorecard=QualityScorecard(
                precision=0.95,
                recall=0.90,
                f1=0.92,
                ece=0.02,
                overall_score=0.92,
                grade="A",
            ),
            reason=["All checks passed"],
            recommendations=["None"],
        )

    def _make_failing_decision(self) -> QualityDecision:
        return QualityDecision(
            status=QualityStatus.RETRY_REQUIRED,
            scorecard=QualityScorecard(
                precision=0.70,
                recall=0.65,
                f1=0.67,
                ece=0.12,
                overall_score=0.67,
                grade="F",
            ),
            reason=["Metrics below threshold"],
            recommendations=["Retry translation"],
            regression_status="FAIL",
            release_decision="BLOCK",
        )

    def test_generate_passing(self):
        gen = FeedbackReportGenerator()
        decision = self._make_passing_decision()
        report = gen.generate(decision)
        assert report.overall_severity == FeedbackSeverity.INFO
        assert report.fail_count == 0
        assert report.source_decision_status == "PASS"

    def test_generate_failing(self):
        gen = FeedbackReportGenerator()
        decision = self._make_failing_decision()
        report = gen.generate(decision)
        assert report.fail_count > 0
        assert report.overall_severity in (FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH)

    def test_report_to_json(self):
        gen = FeedbackReportGenerator()
        report = gen.generate(self._make_passing_decision())
        js = report.to_json()
        parsed = json.loads(js)
        assert "report_id" in parsed
        assert parsed["overall_severity"] == "INFO"

    def test_factory(self):
        gen = create_feedback_report_generator()
        assert isinstance(gen, FeedbackReportGenerator)


class TestSerializer:
    def _make_report(self) -> QualityFeedbackReport:
        from core.knowledge_benchmark.feedback.generator import FeedbackReportGenerator

        gen = FeedbackReportGenerator()
        decision = QualityDecision(
            status=QualityStatus.PASS,
            scorecard=QualityScorecard(
                precision=0.95,
                recall=0.90,
                f1=0.92,
                ece=0.02,
                overall_score=0.92,
                grade="A",
            ),
            reason=["All checks passed"],
            recommendations=["None"],
        )
        return gen.generate(decision)

    def test_serialize_to_json(self):
        report = self._make_report()
        js = serialize_to_json(report)
        parsed = json.loads(js)
        assert parsed["source_decision_status"] == "PASS"
        assert "items" in parsed

    def test_serialize_to_markdown(self):
        report = self._make_report()
        md = serialize_to_markdown(report)
        assert "# Quality Feedback Report" in md
        assert report.report_id in md
        assert "## Summary" in md
        assert "## Rule Evaluations" in md
        assert "## Recommendations" in md
        assert "## Counters" in md

    def test_save_report(self, tmp_path):
        report = self._make_report()
        output_dir = tmp_path / "feedback_reports"
        exported = save_report(report, output_dir, basename="test_feedback")
        assert exported["json"]
        assert exported["markdown"]
        assert Path(exported["json"]).exists()
        assert Path(exported["markdown"]).exists()

        json_content = json.loads(Path(exported["json"]).read_text(encoding="utf-8"))
        assert json_content["report_id"] == report.report_id

        md_content = Path(exported["markdown"]).read_text(encoding="utf-8")
        assert report.report_id in md_content


class TestQualityDecisionConversion:
    def test_passing_decision_feeds_pass_feedback(self):
        from core.knowledge_benchmark.feedback.generator import FeedbackReportGenerator

        decision = QualityDecision(
            status=QualityStatus.PASS,
            scorecard=QualityScorecard(
                precision=0.95,
                recall=0.90,
                f1=0.92,
                ece=0.02,
                overall_score=0.92,
                grade="A",
            ),
            reason=["All checks passed"],
        )

        gen = FeedbackReportGenerator()
        report = gen.generate(decision)

        assert report.fail_count == 0
        assert report.pass_count > 0
        assert len(report.recommendations) == 0

    def test_failing_decision_feeds_actionable_feedback(self):
        from core.knowledge_benchmark.feedback.generator import FeedbackReportGenerator

        decision = QualityDecision(
            status=QualityStatus.RETRY_REQUIRED,
            scorecard=QualityScorecard(
                precision=0.60,
                recall=0.55,
                f1=0.57,
                ece=0.15,
                overall_score=0.57,
                grade="F",
            ),
            reason=["Metrics below all thresholds"],
            recommendations=["Improve extraction quality"],
        )

        gen = FeedbackReportGenerator()
        report = gen.generate(decision)

        assert report.fail_count > 0
        assert len(report.recommendations) > 0


class TestCLIFeedbackIntegration:
    def test_feedback_flag_off_by_default(self):
        import argparse
        from cli.parser import build_parser

        parser = build_parser()
        args = parser.parse_args(["benchmark", "run", "--segments", "1", "--prompts", "1"])
        assert args.feedback is False

    def test_feedback_flag_set(self):
        import argparse
        from cli.parser import build_parser

        parser = build_parser()
        args = parser.parse_args(["benchmark", "run", "--feedback", "--segments", "1", "--prompts", "1"])
        assert args.feedback is True

    def test_feedback_flag_on_runtime(self):
        import argparse
        from cli.parser import build_parser

        parser = build_parser()
        args = parser.parse_args(["benchmark", "runtime", "--feedback", "--segments", "5"])
        assert args.feedback is True
        assert args.benchmark_action == "runtime"

    def test_feedback_flag_on_compare(self):
        import argparse
        from cli.parser import build_parser

        parser = build_parser()
        args = parser.parse_args(["benchmark", "compare", "--feedback", "--baseline", "/tmp/foo.json", "--threshold", "0.05"])
        assert args.feedback is True
        assert args.benchmark_action == "compare"
        assert args.threshold == 0.05