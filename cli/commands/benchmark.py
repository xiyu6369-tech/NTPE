from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .manifest import attach_benchmark_manifest


def _result_dicts(results: Iterable[Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for item in results:
        if hasattr(item, "to_dict"):
            items.append(dict(item.to_dict()))
        elif isinstance(item, Mapping):
            items.append(dict(item))
        else:
            items.append({"name": str(item), "status": "PASS", "metrics": {}})
    return items


def _ensure_report_dir(context: CLIContext, output: str | None = None) -> Path:
    path = Path(output) if output else context.path("benchmark_reports")
    if not path.is_absolute():
        path = context.root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _build_report(results: Iterable[Any], title: str = "NTPE CLI Benchmark Report") -> Dict[str, Any]:
    from benchmark.report.report_builder import build_performance_report

    return build_performance_report(results, metadata={"source": "cli.benchmark", "stage": "beta-stage-06.3"}) | {"title": title}


def _export_report(report: Dict[str, Any], output_dir: Path, basename: str = "benchmark") -> Dict[str, str]:
    from benchmark.report.report_exporter import export_performance_report

    exported = export_performance_report(report, output_dir, basename=basename)
    return {key: str(value) for key, value in exported.items()}


def _run_runtime(args: object) -> List[Any]:
    from benchmark.runtime.runtime_benchmark import run_runtime_benchmark

    segments = range(int(getattr(args, "segments", 10) or 10))
    return list(run_runtime_benchmark(segments=segments))


def _run_provider(args: object) -> List[Any]:
    from benchmark.provider.provider_benchmark import run_provider_benchmark

    prompts = [f"benchmark prompt {index}" for index in range(int(getattr(args, "prompts", 3) or 3))]
    return list(run_provider_benchmark(prompts=prompts))


def _run_stress(args: object) -> List[Any]:
    from benchmark.stress.soak_runner import run_soak_benchmark
    from benchmark.stress.stress_runner import run_stress_benchmark

    segments = int(getattr(args, "segments", 25) or 25)
    iterations = int(getattr(args, "iterations", 2) or 2)
    return [run_stress_benchmark(segment_count=segments), run_soak_benchmark(iterations=iterations, segment_count=max(1, min(segments, 10)))]


def _run_all(args: object) -> List[Any]:
    return [*_run_runtime(args), *_run_provider(args), *_run_stress(args)]


def _generate_feedback_report(data: Dict[str, Any], output_dir: Path, args: object) -> None:
    if not getattr(args, "feedback", False):
        return
    from core.knowledge_benchmark.feedback import (
        FeedbackReportGenerator,
        save_report,
    )
    from core.knowledge_benchmark.runtime.models import (
        QualityDecision,
        QualityStatus,
        QualityScorecard,
    )

    summary = data.get("summary", {})
    overall_score = float(summary.get("overall_score", 0.0))
    grade = str(summary.get("grade", "F"))
    precision = float(summary.get("precision", 0.0))
    recall = float(summary.get("recall", 0.0))
    f1 = float(summary.get("f1", 0.0))
    ece = float(summary.get("ece", 0.0))
    failed_count = int(summary.get("failed", 0) or 0)

    status = QualityStatus.RETRY_REQUIRED if failed_count > 0 else QualityStatus.PASS
    decision = QualityDecision(
        status=status,
        scorecard=QualityScorecard(
            precision=precision,
            recall=recall,
            f1=f1,
            ece=ece,
            overall_score=overall_score,
            grade=grade,
        ),
        reason=["CLI benchmark feedback report generated from benchmark results"],
        recommendations=[],
    )

    generator = FeedbackReportGenerator()
    report = generator.generate(decision)
    exported = save_report(report, output_dir, basename="quality_feedback")
    data["feedback"] = {"report": report.to_dict(), "exported": exported}
    data["feedback_report"] = report.to_dict()


def _success_payload(context: CLIContext, args: object, results: List[Any], *, message: str, basename: str) -> CLIResult:
    output_dir = _ensure_report_dir(context, getattr(args, "output", None))
    report = _build_report(results, title=message)
    exported = _export_report(report, output_dir, basename=basename)
    data: Dict[str, Any] = {
        "results": _result_dicts(results),
        "summary": report.get("summary", {}),
        "report": report,
        "exported": exported,
    }
    attach_benchmark_manifest(data)
    _generate_feedback_report(data, output_dir, args)
    failed = int(report.get("summary", {}).get("failed", 0) or 0)
    if failed:
        return CLIResult.failure(message + " failed", exit_code=2, errors=[f"{failed} benchmark(s) failed"], **data)
    return CLIResult.success(message, **data)


def command_benchmark(context: CLIContext, args: object) -> CLIResult:
    action = getattr(args, "benchmark_action", None) or "run"
    try:
        if action == "runtime":
            return _success_payload(context, args, _run_runtime(args), message="Runtime benchmark completed", basename="runtime_benchmark")
        if action == "provider":
            return _success_payload(context, args, _run_provider(args), message="Provider benchmark completed", basename="provider_benchmark")
        if action == "stress":
            return _success_payload(context, args, _run_stress(args), message="Stress benchmark completed", basename="stress_benchmark")
        if action == "report":
            return command_benchmark_report(context, args)
        if action == "compare":
            return command_benchmark_compare(context, args)
        return _success_payload(context, args, _run_all(args), message="Benchmark completed", basename="benchmark")
    except Exception as exc:
        return CLIResult.failure(f"Benchmark failed: {exc}", exit_code=2)


def _read_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def command_benchmark_report(context: CLIContext, args: object) -> CLIResult:
    source = getattr(args, "source", None)
    if source:
        report = _read_json(source)
    else:
        report = _build_report(_run_all(args), title="NTPE Benchmark Report")
    output_dir = _ensure_report_dir(context, getattr(args, "output", None))
    exported = _export_report(report, output_dir, basename=getattr(args, "basename", "benchmark_report") or "benchmark_report")
    data = {"report": report, "summary": report.get("summary", {}), "exported": exported}
    attach_benchmark_manifest(data)
    _generate_feedback_report(data, output_dir, args)
    return CLIResult.success("Benchmark report generated", **data)


def command_benchmark_compare(context: CLIContext, args: object) -> CLIResult:
    from benchmark.report.regression_report import build_regression_report

    baseline = _read_json(getattr(args, "baseline"))
    current_arg = getattr(args, "current", None)
    current = _read_json(current_arg) if current_arg else _build_report(_run_all(args), title="Current Benchmark")
    regression = build_regression_report(baseline, current, threshold=float(getattr(args, "threshold", 0.10) or 0.10))
    output_dir = _ensure_report_dir(context, getattr(args, "output", None))
    output_file = output_dir / "regression.json"
    output_file.write_text(json.dumps(regression, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    data = {"regression": regression, "exported": {"json": str(output_file)}}
    attach_benchmark_manifest(data)
    _generate_feedback_report(data, output_dir, args)
    status = regression.get("status", "PASS")
    if status == "REGRESSION":
        return CLIResult.failure("Benchmark regression detected", exit_code=2, errors=["performance regression detected"], **data)
    return CLIResult.success("Benchmark comparison completed", **data)


def register_benchmark_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("benchmark", "run NTPE benchmark suites", command_benchmark))
    return registry
