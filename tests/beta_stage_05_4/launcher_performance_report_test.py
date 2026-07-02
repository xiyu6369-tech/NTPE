from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.benchmark_registry import BenchmarkRegistry
from benchmark.benchmark_runner import BenchmarkRunner
from benchmark.benchmark_suite import BenchmarkSuite
from benchmark.benchmark_case import FunctionBenchmarkCase
from benchmark.report import (
    DashboardBuilder,
    HTMLReportRenderer,
    JSONReportRenderer,
    PerformanceReportBuilder,
    PerformanceReportExporter,
    RegressionAnalyzer,
    TrendAnalyzer,
    analyze_trends,
    attach_performance_report_manifest,
    build_dashboard,
    build_performance_report,
    build_regression_report,
    export_performance_report,
    get_performance_report_manifest,
    render_html_report,
    render_json_report,
)


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def sample_results():
    return [
        BenchmarkResult(
            name="runtime_startup",
            status=BenchmarkStatus.PASS,
            elapsed_ms=10.0,
            peak_memory_bytes=100,
            metrics={"category": "runtime", "throughput": 5},
        ),
        BenchmarkResult(
            name="provider_latency",
            status=BenchmarkStatus.PASS,
            elapsed_ms=20.0,
            peak_memory_bytes=200,
            metrics={"category": "provider", "latency_ms": 20},
        ),
        BenchmarkResult(
            name="stress_runner",
            status=BenchmarkStatus.PASS,
            elapsed_ms=30.0,
            peak_memory_bytes=300,
            metrics={"category": "stress", "segments": 50},
        ),
    ]


def main() -> None:
    results = sample_results()

    builder = PerformanceReportBuilder(metadata={"stage": "05.4"})
    report = builder.build(results)
    show("Report Builder", report["summary"]["total"] == 3 and report["summary"]["status"] == "PASS")

    report2 = build_performance_report(results)
    show("Benchmark Summary", report2["categories"]["runtime"]["count"] == 1)

    json_text = JSONReportRenderer().render(report)
    loaded = json.loads(json_text)
    show("JSON Report", loaded["schema"] == "ntpe.performance.report.v1")

    html_text = HTMLReportRenderer().render(report)
    show("HTML Report", "<html" in html_text and "runtime_startup" in html_text)

    show("Render Helpers", "provider_latency" in render_html_report(report) and json.loads(render_json_report(report))["summary"]["total"] == 3)

    with tempfile.TemporaryDirectory() as tmp:
        exported = PerformanceReportExporter().export(report, tmp)
        show("Report Exporter", exported["json"].exists() and exported["html"].exists())
        exported2 = export_performance_report(report, tmp, basename="dashboard")
        show("Export Helper", exported2["json"].name == "dashboard.json")

    baseline = dict(report)
    baseline["summary"] = dict(report["summary"])
    baseline["summary"]["elapsed_ms"] = 100.0
    current = dict(report)
    current["summary"] = dict(report["summary"])
    current["summary"]["elapsed_ms"] = 80.0
    regression = RegressionAnalyzer(threshold=0.10).compare(baseline, current)
    show("Regression Report", regression["status"] == "PASS" and regression["findings"][0]["status"] == "IMPROVEMENT")

    regression2 = build_regression_report(current, baseline, threshold=0.10)
    show("Regression Helper", regression2["status"] == "REGRESSION")

    trend = TrendAnalyzer().analyze([baseline, current])
    show("Trend Analyzer", trend["count"] == 2 and trend["direction"] == "down")

    trend2 = analyze_trends([baseline, current])
    show("Trend Helper", trend2["average"] == 90.0)

    dashboard = DashboardBuilder().build(report, regression, trend)
    show("Dashboard", dashboard["schema"] == "ntpe.performance.dashboard.v1" and dashboard["status"] == "PASS")

    dashboard2 = build_dashboard(report)
    show("Dashboard Helper", dashboard2["summary"]["passed"] == 3)

    manifest = get_performance_report_manifest()
    show("Performance Manifest", manifest["stage"] == "beta-stage-05.4" and manifest["backward_compatible"])

    attached = attach_performance_report_manifest({"runtime": "ok"})
    show("Manifest Helper", attached["performance_report"]["foundation_compatible"] is True)

    registry = BenchmarkRegistry()
    registry.register(FunctionBenchmarkCase("report_case", lambda ctx: {"category": "report", "value": 1}))
    reg_results = BenchmarkRunner().run_registry(registry)
    show("Benchmark Registry", len(reg_results) == 1 and reg_results[0].is_passed())

    suite = BenchmarkSuite(name="report_suite")
    suite.add(FunctionBenchmarkCase("dashboard_case", lambda ctx: build_dashboard(report)["summary"]))
    suite_results = BenchmarkRunner().run_suite(suite)
    show("Benchmark Suite", len(suite_results) == 1 and suite_results[0].metrics["total"] == 3)

    show("Integration Test", report["categories"]["provider"]["passed"] == 1 and regression["schema"].endswith("v1"))
    show("Backward Compatible", manifest["foundation_compatibility"] == "foundation-v1.0-frozen")
    print("PASS")


if __name__ == "__main__":
    main()
