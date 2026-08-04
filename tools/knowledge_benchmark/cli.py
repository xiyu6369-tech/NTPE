"""CLI for Knowledge Benchmark Runner (RM-5.8.3)

Entry point for running offline knowledge benchmarks.
Supports single and all-extractor benchmarking plus regression comparison.

Usage:
    python -m tools.knowledge_benchmark.cli --all
    python -m tools.knowledge_benchmark.cli --extractor character
    python -m tools.knowledge_benchmark.cli --all --compare-baseline
    python runner.py --all
    python runner.py --extractor glossary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runner import Runner, ALL_EXTRACTORS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NTPE Knowledge Benchmark Runner (RM-5.8.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python runner.py --all
  python runner.py --extractor character
  python runner.py --all --compare-baseline
  python runner.py --extractor glossary --output results/custom""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run all extractors (character, glossary, scene, narrative, style)")
    group.add_argument("--extractor", type=str, choices=ALL_EXTRACTORS, help="Run a single extractor")
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

    output_dir = runner.writer.output_dir.resolve()
    print(f"\nResults written to: {output_dir}")
    print("Done.")


if __name__ == "__main__":
    main()