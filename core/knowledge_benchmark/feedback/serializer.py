"""
Quality Feedback Report Serializer (RM-5.9.2)

Serializes QualityFeedbackReport to JSON and Markdown formats.

Offline. Zero external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import FeedbackRuleStatus, QualityFeedbackReport


def serialize_to_json(report: QualityFeedbackReport, indent: int = 2) -> str:
    return report.to_json(indent=indent)


def serialize_to_markdown(report: QualityFeedbackReport) -> str:
    lines = [
        "# Quality Feedback Report",
        "",
        f"**Report ID**: `{report.report_id}`",
        f"**Generated At**: `{report.generated_at}`",
        f"**Source Decision**: `{report.source_decision_status}`",
        f"**Overall Severity**: `{report.overall_severity.value}`",
        "",
        "---",
        "",
        "## Source Decision Rationale",
        "",
        report.source_decision_rationale,
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    for line in report.summary:
        lines.append(f"- {line}")

    lines.extend([
        "",
        "---",
        "",
        "## Rule Evaluations",
        "",
        "| Rule | Metric | Current | Target | Delta | Status | Severity |",
        "|------|--------|---------|--------|-------|--------|----------|",
    ])

    for item in report.items:
        status_icon = {
            FeedbackRuleStatus.PASS: "PASS",
            FeedbackRuleStatus.FAIL: "FAIL",
            FeedbackRuleStatus.WARNING: "WARN",
            FeedbackRuleStatus.SKIPPED: "SKIP",
        }.get(item.status, "?")
        lines.append(
            f"| {item.rule_id} | {item.metric} | {item.current_value:.4f} | {item.target_value:.4f} | {item.delta:+.4f} | {status_icon} | {item.severity.value} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        "",
    ])

    for rec in report.recommendations:
        lines.append(f"- {rec}")

    if not report.recommendations:
        lines.append("No actionable recommendations.")

    lines.extend([
        "",
        "---",
        "",
        "## Counters",
        "",
        f"- Passed: {report.pass_count}",
        f"- Failed: {report.fail_count}",
        f"- Warnings: {report.warning_count}",
        f"- Critical: {report.critical_count}",
    ])

    return "\n".join(lines)


def save_report(
    report: QualityFeedbackReport,
    output_dir: Path,
    basename: str = "quality_feedback_report",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{basename}.json"
    json_path.write_text(serialize_to_json(report), encoding="utf-8")

    md_path = output_dir / f"{basename}.md"
    md_path.write_text(serialize_to_markdown(report), encoding="utf-8")

    return {"json": str(json_path), "markdown": str(md_path)}