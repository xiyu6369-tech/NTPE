"""CLI for Knowledge Benchmark Runner (RM-5.8.3 / RM-5.8.4)

Entry point for running offline knowledge benchmarks and analysis.
Supports single and all-extractor benchmarking, regression comparison,
and full analysis (failure classification, statistics, suggestions, trends).

Usage:
    python -m tools.knowledge_benchmark.cli --all
    python -m tools.knowledge_benchmark.cli --all --analysis
    python -m tools.knowledge_benchmark.cli --all --analysis --compare-baseline
    python runner.py --all
    python runner.py --extractor glossary --analysis
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runner import Runner, ALL_EXTRACTORS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NTPE Knowledge Benchmark Runner (RM-5.8.3) + Analysis Engine (RM-5.8.4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python runner.py --all
  python runner.py --extractor character --analysis
  python runner.py --all --compare-baseline --analysis
  python runner.py --analysis
  python runner.py --analysis --compare-baseline""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run all extractors (character, glossary, scene, narrative, style)")
    group.add_argument("--extractor", type=str, choices=ALL_EXTRACTORS, help="Run a single extractor")
    parser.add_argument("--analysis", action="store_true", help="Enable Analysis Engine (RM-5.8.4)")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare against baseline results")
    parser.add_argument("--output", type=str, default="benchmarks/results/current", help="Output directory for results")
    parser.add_argument("--baseline", type=str, default="benchmarks/results/baseline", help="Baseline directory for comparison")
    parser.add_argument("--root", type=str, default=".", help="Project root directory")

    args = parser.parse_args()

    runner = Runner(root_path=Path(args.root))

    if args.output:
        runner.writer.output_dir = Path(args.root) / args.output
    if args.baseline:
        runner.writer.baseline_dir = Path(args.root) / args.baseline

    if args.all:
        print("Running all extractors...")
        results = runner.run_all()
    elif args.extractor:
        print(f"Running {args.extractor} extractor...")
        results = {args.extractor: runner.run_extractor(args.extractor)}

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
            print(f"  {detail['extractor']}: baseline_f1={detail['baseline_f1']:.4f}, current_f1={detail['current_f1']:.4f}, delta={detail['delta']:+.4f} [{status}]")

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

            out_dir = Path(args.root) / args.output
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

    output_dir = runner.writer.output_dir.resolve()
    print(f"\nResults written to: {output_dir}")
    print("Done.")


if __name__ == "__main__":
    main()