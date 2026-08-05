"""CLI for Knowledge Benchmark Runner (RM-5.8.5)

Entry point for running offline knowledge benchmarks, analysis,
dashboard generation, baseline management, history browsing, and release gate.

Usage:
    python -m tools.knowledge_benchmark.cli --all
    python -m tools.knowledge_benchmark.cli --all --analysis
    python -m tools.knowledge_benchmark.cli --dashboard
    python -m tools.knowledge_benchmark.cli --promote-baseline
    python -m tools.knowledge_benchmark.cli --history
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .runner import Runner, ALL_EXTRACTORS


def _cmd_dashboard(args, runner: Runner, root: Path) -> None:
    print("Generating Dashboard (RM-5.8.5)...")

    output_dir = root / args.output
    overall_path = output_dir / "overall_scorecard.json"
    if not overall_path.is_file():
        print(f"ERROR: No scorecard found at {overall_path}")
        print("Run benchmark first: python -m tools.knowledge_benchmark.cli --all")
        return

    overall_data = json.loads(overall_path.read_text(encoding="utf-8"))
    regression_check = overall_data.get("regression_check")

    from core.knowledge_benchmark.dashboard import create_dashboard_generator
    generator = create_dashboard_generator()
    dashboard = generator.build_from_scorecard(overall_data, regression_check)
    paths = generator.write_dashboard(dashboard)

    print(f"Dashboard written to: {paths['markdown']}")
    print(f"Dashboard JSON: {paths['json']}")
    print(f"Overall Score: {dashboard.overall_score:.4f} ({dashboard.overall_grade})")


def _cmd_promote_baseline(args, runner: Runner, root: Path) -> None:
    print("Promoting current results to Baseline...")

    output_dir = root / args.output
    overall_path = output_dir / "overall_scorecard.json"
    if not overall_path.is_file():
        print(f"ERROR: No scorecard found at {overall_path}")
        return

    overall_data = json.loads(overall_path.read_text(encoding="utf-8"))
    run_id = overall_data.get("metadata", {}).get("benchmark_id", "unknown")

    from core.knowledge_benchmark.baseline.manager import create_baseline_manager
    manager = create_baseline_manager()
    entry = manager.promote(run_id, overall_data)

    runner.writer.save_current_as_baseline()

    print(f"Baseline promoted: {entry.baseline_id}")
    print(f"  Run: {entry.run_id}")
    print(f"  Score: {entry.overall_score:.4f} ({entry.grade})")
    print(f"  Extractor scores: {json.dumps(entry.extractor_scores, indent=2)}")


def _cmd_history(args, runner: Runner, root: Path) -> None:
    print("History:")
    print()

    entries = runner.writer.list_history()

    if not entries:
        from core.knowledge_benchmark.baseline.manager import create_baseline_manager
        manager = create_baseline_manager()
        baselines = manager.list_baselines()
        bl_list = baselines.get("baselines", [])
        if bl_list:
            print("Baseline History:")
            header = f"  {'ID':<36} {'Score':<8} {'Grade':<5} {'Status':<12}"
            print(header)
            print(f"  {'-'*36} {'-'*8} {'-'*5} {'-'*12}")
            for b in bl_list:
                print(f"  {b['baseline_id']:<36} {b['overall_score']:.4f}   {b['grade']:<5} {b['status']:<12}")
        else:
            print("No history entries found.")
            print("Run benchmarks first: python -m tools.knowledge_benchmark.cli --all")
        return

    print(f"  {'Run':<28} {'Score':<10} {'Grade':<6}")
    print(f"  {'-'*28} {'-'*10} {'-'*6}")
    for entry in entries:
        score_str = f"{entry['overall_score']:.4f}" if entry['overall_score'] is not None else "N/A"
        print(f"  {entry['directory']:<28} {score_str:<10} {entry['grade']:<6}")

    from core.knowledge_benchmark.baseline.manager import create_baseline_manager
    manager = create_baseline_manager()
    baselines = manager.list_baselines()
    bl_list = baselines.get("baselines", [])
    if bl_list:
        print()
        print("Baselines:")
        print(f"  {'ID':<36} {'Score':<8} {'Grade':<5} {'Status':<12}")
        print(f"  {'-'*36} {'-'*8} {'-'*5} {'-'*12}")
        for b in bl_list:
            print(f"  {b['baseline_id']:<36} {b['overall_score']:.4f}   {b['grade']:<5} {b['status']:<12}")


def _cmd_regression_gate(args, runner: Runner, root: Path) -> None:
    print("Evaluating Regression Gate...")

    output_dir = root / args.output
    overall_path = output_dir / "overall_scorecard.json"
    if not overall_path.is_file():
        print(f"ERROR: No scorecard found at {overall_path}")
        return

    overall_data = json.loads(overall_path.read_text(encoding="utf-8"))

    from core.knowledge_benchmark.baseline.manager import create_baseline_manager
    manager = create_baseline_manager()
    baseline = manager.load_baseline()

    if baseline is None:
        print("No baseline found. Promote first: python -m tools.knowledge_benchmark.cli --promote-baseline")
        return

    current_scores: Dict[str, Dict[str, float]] = {}
    overall = overall_data.get("overall", {})
    for ext_name, ext_sc in overall.get("extractor_scores", {}).items():
        current_scores[ext_name] = {
            metric: ms.get("value", 0.0) if isinstance(ms, dict) else ms
            for metric, ms in ext_sc.get("metric_scores", {}).items()
        }

    baseline_scores: Dict[str, Dict[str, float]] = {}
    for snapshot in baseline.metric_snapshots:
        ext = snapshot.extractor_type
        if ext not in baseline_scores:
            baseline_scores[ext] = {}
        baseline_scores[ext][snapshot.metric_name] = snapshot.score

    from core.knowledge_benchmark.regression_gate import create_regression_gate
    gate = create_regression_gate()
    report = gate.evaluate(current_scores, baseline_scores)

    print(f"\nRegression Gate: **{report.overall_status.value}**")
    print(f"  Pass Release: {report.pass_release}")
    print(f"  Failures: {report.failure_count}, Warnings: {report.warning_count}")
    print()
    print(f"  {'Extractor':<14} {'Metric':<22} {'Current':<10} {'Baseline':<10} {'Delta':<10} {'Delta%':<10} {'Status':<10}")
    print(f"  {'-'*14} {'-'*22} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for c in report.comparisons:
        delta_pct_str = f"{c.delta_percent:+.2f}%"
        print(f"  {c.extractor_type:<14} {c.metric_name:<22} {c.current_value:<10.4f} {c.baseline_value:<10.4f} {c.delta:<+10.4f} {delta_pct_str:<10} {c.status.value:<10}")

    gate_path = output_dir / "regression_gate_report.json"
    gate_path.write_text(report.to_json(), encoding="utf-8")
    print(f"\nRegression gate report: {gate_path}")


def _cmd_runtime_check(args, runner: Runner, root: Path) -> None:
    print("Runtime Quality Gate Check (RM-5.9.1)")
    print("=" * 50)
    print()

    from core.knowledge_benchmark.runtime.adapter import create_runtime_adapter
    from core.knowledge_benchmark.runtime.models import (
        TranslationInput,
        KnowledgeExtractionOutput,
    )

    adapter = create_runtime_adapter()

    sample_source = "The customer service representative greeted the client warmly and processed the purchase."
    sample_translation = "客服人员热情地迎接了客户并处理了购买事宜。"

    sample_entities = [
        {"id": "ent_1", "type": "character", "name": "customer_service", "attributes": ["polite", "professional"]},
        {"id": "ent_2", "type": "character", "name": "client", "attributes": []},
    ]

    predicted_entities = [
        {"id": "ent_1", "type": "character", "name": "customer_service", "attributes": ["polite"]},
        {"id": "ent_100", "type": "character", "name": "purchase", "attributes": []},
    ]

    translation = TranslationInput(
        source_text=sample_source,
        translated_text=sample_translation,
        metadata={"mode": "test"},
    )
    extraction = KnowledgeExtractionOutput(
        source_text=sample_translation,
        extracted_entities=predicted_entities,
        extractor_type="character",
    )

    decision = adapter.evaluate(
        translation=translation,
        extraction=extraction,
        golden_entities=sample_entities,
        extractor_type="character",
    )

    print(f"Status       : {decision.status.value}")
    print(f"Release      : {decision.release_decision}")
    print(f"Regression   : {decision.regression_status}")
    print(f"Pass Gate    : {decision.pass_gate}")
    print(f"Require Retry: {decision.requires_retry}")
    print()
    print("Scorecard:")
    print(f"  Precision  : {decision.scorecard.precision:.4f}")
    print(f"  Recall     : {decision.scorecard.recall:.4f}")
    print(f"  F1         : {decision.scorecard.f1:.4f}")
    print(f"  ECE        : {decision.scorecard.ece:.4f}")
    print(f"  Overall    : {decision.scorecard.overall_score:.4f} ({decision.scorecard.grade})")
    if decision.reason:
        print(f"\nReasons:")
        for r in decision.reason:
            print(f"  - {r}")
    if decision.recommendations:
        print(f"\nRecommendations:")
        for r in decision.recommendations:
            print(f"  - {r}")

    output_dir = root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = output_dir / "runtime_quality_decision.json"
    decision_path.write_text(decision.to_json(), encoding="utf-8")
    print(f"\nDecision saved to: {decision_path}")


def _cmd_release_gate(args, runner: Runner, root: Path) -> None:
    print("Evaluating Release Gate...")

    output_dir = root / args.output
    overall_path = output_dir / "overall_scorecard.json"
    if not overall_path.is_file():
        print(f"ERROR: No scorecard found at {overall_path}")
        return

    overall_data = json.loads(overall_path.read_text(encoding="utf-8"))

    gate_path = output_dir / "regression_gate_report.json"
    regression_report = None
    if gate_path.is_file():
        regression_report = json.loads(gate_path.read_text(encoding="utf-8"))

    from core.knowledge_benchmark.baseline.manager import create_baseline_manager
    manager = create_baseline_manager()
    baseline = manager.load_baseline()
    baseline_score = baseline.overall_score if baseline else None

    from core.knowledge_benchmark.release_gate import create_release_gate
    release = create_release_gate()
    result = release.evaluate(overall_data, regression_report, baseline_score)

    print(f"\nRelease Gate: **{result.decision.value}**")
    print(f"  Reason: {result.reason}")
    print(f"  Overall Score: {result.overall_score:.4f}")
    if baseline_score is not None:
        print(f"  Score Change: {result.overall_score - result.baseline_score:+.4f}")
    print(f"  Regression Passed: {result.regression_passed}")
    print(f"  Score Above Threshold: {result.score_threshold_passed}")
    if result.recommendations:
        print("  Recommendations:")
        for rec in result.recommendations:
            print(f"    - {rec}")

    release_path = output_dir / "release_gate_result.json"
    release_path.write_text(result.to_json(), encoding="utf-8")
    print(f"\nRelease gate result: {release_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NTPE Knowledge Benchmark Runner (RM-5.8.5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python -m tools.knowledge_benchmark.cli --all
  python -m tools.knowledge_benchmark.cli --extractor character --analysis
  python -m tools.knowledge_benchmark.cli --all --compare-baseline --analysis
  python -m tools.knowledge_benchmark.cli --dashboard
  python -m tools.knowledge_benchmark.cli --promote-baseline
  python -m tools.knowledge_benchmark.cli --history
  python -m tools.knowledge_benchmark.cli --regression-gate
  python -m tools.knowledge_benchmark.cli --release-gate
  python -m tools.knowledge_benchmark.cli --runtime-check""",
    )

    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--all", action="store_true", help="Run all extractors")
    run_group.add_argument("--extractor", type=str, choices=ALL_EXTRACTORS, help="Run a single extractor")
    run_group.add_argument("--dashboard", action="store_true", help="Generate Dashboard (RM-5.8.5)")
    run_group.add_argument("--promote-baseline", action="store_true", help="Promote current results to Baseline")
    run_group.add_argument("--history", action="store_true", help="Show benchmark history")
    run_group.add_argument("--regression-gate", action="store_true", help="Run Regression Gate check")
    run_group.add_argument("--release-gate", action="store_true", help="Run Release Gate check")
    run_group.add_argument("--runtime-check", action="store_true", help="Run Runtime Quality Gate check (RM-5.9.1)")

    parser.add_argument("--analysis", action="store_true", help="Enable Analysis Engine (RM-5.8.4)")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare against baseline results")
    parser.add_argument("--output", type=str, default="benchmarks/results/current", help="Output directory")
    parser.add_argument("--baseline", type=str, default="benchmarks/results/baseline", help="Baseline directory")
    parser.add_argument("--root", type=str, default=".", help="Project root directory")

    args = parser.parse_args()
    root = Path(args.root)

    if args.dashboard:
        runner = Runner(root_path=root)
        runner.writer.output_dir = root / args.output
        _cmd_dashboard(args, runner, root)
        return

    if args.promote_baseline:
        runner = Runner(root_path=root)
        runner.writer.output_dir = root / args.output
        runner.writer.baseline_dir = root / args.baseline
        _cmd_promote_baseline(args, runner, root)
        return

    if args.history:
        runner = Runner(root_path=root)
        _cmd_history(args, runner, root)
        return

    if args.regression_gate:
        runner = Runner(root_path=root)
        runner.writer.output_dir = root / args.output
        _cmd_regression_gate(args, runner, root)
        return

    if args.release_gate:
        runner = Runner(root_path=root)
        runner.writer.output_dir = root / args.output
        _cmd_release_gate(args, runner, root)
        return

    if args.runtime_check:
        runner = Runner(root_path=root)
        runner.writer.output_dir = root / args.output
        _cmd_runtime_check(args, runner, root)
        return

    runner = Runner(root_path=root)
    runner.writer.output_dir = root / args.output
    runner.writer.baseline_dir = root / args.baseline

    if args.all:
        print("Running all extractors...")
        results = runner.run_all()
    elif args.extractor:
        print(f"Running {args.extractor} extractor...")
        results = {args.extractor: runner.run_extractor(args.extractor)}
    else:
        print("No action specified. Use --all, --dashboard, --promote-baseline, etc.")
        sys.exit(1)

    print()
    for name, result in results.items():
        if result.success:
            score_str = ""
            if result.extractor_score:
                score_str = f", score={result.extractor_score.extractor_score:.4f}"
            print(f"  {name}: PASSED ({result.passed_cases}/{result.total_cases} cases{score_str})")
        else:
            print(f"  {name}: FAILED - {', '.join(result.errors[:3])}")

    if args.compare_baseline:
        regression = runner.check_regression(results)
        print(f"\nRegression Check: {regression['result']}")
        for detail in regression.get("details", []):
            status = "PASS" if detail["status"] == "pass" else "FAIL"
            print(f"  {detail['extractor']}: baseline_f1={detail['baseline_f1']:.4f}, "
                  f"current_f1={detail['current_f1']:.4f}, delta={detail['delta']:+.4f} [{status}]")

    runner.write_outputs(results, compare_baseline=args.compare_baseline)

    if args.analysis:
        print("\nRunning Analysis Engine (RM-5.8.4)...")

        all_comparisons = []
        for result in results.values():
            if result.success and result.comparisons:
                all_comparisons.extend(result.comparisons)

        if all_comparisons:
            baseline_results = None
            if args.compare_baseline:
                baseline_results = {}
                for ext_name in results:
                    bl = runner.writer.load_baseline(ext_name)
                    if bl:
                        nested = bl.get("overall", {}).get("extractor_scores", {})
                        for et_n, et_sc in nested.items():
                            ms = et_sc.get("metric_scores", {})
                            baseline_results[ext_name] = {
                                mn: m.get("value", 0.0) if isinstance(m, dict) else 0.0
                                for mn, m in ms.items()
                            }

            from core.knowledge_benchmark.analysis.orchestrator import create_analyzer
            analyzer = create_analyzer()
            report = analyzer.analyze(
                comparisons=all_comparisons,
                baseline_results=baseline_results,
            )

            out_dir = root / args.output
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "analysis_report.md").write_text(report.to_markdown(), encoding="utf-8")
            (out_dir / "analysis_report.json").write_text(report.to_json(), encoding="utf-8")

            print(f"\nAnalysis Report written to: {out_dir / 'analysis_report.md'}")
            print(f"Analysis JSON: {out_dir / 'analysis_report.json'}")

            if report.failure_summary.total_failures > 0:
                top_category = max(
                    report.failure_summary.by_category.items(),
                    key=lambda x: x[1],
                    default=("N/A", 0),
                )
                print(f"Failure Summary: {report.failure_summary.total_failures} failures")
                print(f"Top Failure Type: {top_category[0]} ({top_category[1]} instances)")
                print(f"Suggestions: {len(report.suggestions)} actionable items")
            else:
                print("Analysis complete. No failures detected.")
        else:
            print("No comparisons available for analysis.")

    print(f"\nResults written to: {runner.writer.output_dir.resolve()}")
    print("Done.")


if __name__ == "__main__":
    main()