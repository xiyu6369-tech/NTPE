from __future__ import annotations

import argparse


def _global_options() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--json", action="store_true", dest="as_json", help="print command result as JSON")
    parent.add_argument("--root", default=None, help="project root directory")
    return parent


def build_parser() -> argparse.ArgumentParser:
    common = _global_options()
    parser = argparse.ArgumentParser(
        prog="ntpe",
        description="NTPE command line interface",
        parents=[common],
    )

    subparsers = parser.add_subparsers(dest="command")

    version = subparsers.add_parser("version", help="show NTPE version", parents=[common])
    version.set_defaults(command="version")

    doctor = subparsers.add_parser("doctor", help="check project structure and CLI readiness", parents=[common])
    doctor.add_argument("--strict", action="store_true", help="fail if recommended directories are missing")
    doctor.set_defaults(command="doctor")

    translate = subparsers.add_parser("translate", help="translate a TXT file or a folder", parents=[common])
    translate.add_argument("input", help="TXT file or folder to translate")
    translate.add_argument("--output", "-o", default=None, help="output directory")
    translate.add_argument("--resume", action="store_true", help="skip existing outputs")
    translate.add_argument("--provider", default="mock", help="provider name, e.g. nvidia/openai/gemini/mock")
    translate.add_argument("--quality", default="standard", help="quality profile, e.g. draft/standard/high")
    translate.add_argument("--dry-run", action="store_true", help="scan and plan without writing outputs")
    translate.add_argument("--pattern", default="*.txt", help="file glob when input is a folder")
    translate.add_argument("--overwrite", action="store_true", help="overwrite existing outputs")
    translate.add_argument("--suffix", default="_zh", help="output filename suffix")
    translate.set_defaults(command="translate")

    benchmark = subparsers.add_parser("benchmark", help="run NTPE benchmark suites", parents=[common])
    benchmark_sub = benchmark.add_subparsers(dest="benchmark_action")

    benchmark_run = benchmark_sub.add_parser("run", help="run all benchmark suites", parents=[common])
    benchmark_run.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_run.add_argument("--segments", type=int, default=25, help="number of synthetic segments")
    benchmark_run.add_argument("--prompts", type=int, default=3, help="number of synthetic provider prompts")
    benchmark_run.add_argument("--iterations", type=int, default=2, help="soak test iterations")
    benchmark_run.set_defaults(command="benchmark", benchmark_action="run")

    benchmark_runtime = benchmark_sub.add_parser("runtime", help="run runtime benchmark", parents=[common])
    benchmark_runtime.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_runtime.add_argument("--segments", type=int, default=10, help="number of synthetic segments")
    benchmark_runtime.set_defaults(command="benchmark", benchmark_action="runtime")

    benchmark_provider = benchmark_sub.add_parser("provider", help="run provider benchmark", parents=[common])
    benchmark_provider.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_provider.add_argument("--prompts", type=int, default=3, help="number of synthetic provider prompts")
    benchmark_provider.set_defaults(command="benchmark", benchmark_action="provider")

    benchmark_stress = benchmark_sub.add_parser("stress", help="run stress and soak benchmark", parents=[common])
    benchmark_stress.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_stress.add_argument("--segments", type=int, default=25, help="number of synthetic segments")
    benchmark_stress.add_argument("--iterations", type=int, default=2, help="soak test iterations")
    benchmark_stress.set_defaults(command="benchmark", benchmark_action="stress")

    benchmark_report = benchmark_sub.add_parser("report", help="generate performance report", parents=[common])
    benchmark_report.add_argument("--source", default=None, help="existing benchmark JSON report")
    benchmark_report.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_report.add_argument("--basename", default="benchmark_report", help="report basename")
    benchmark_report.set_defaults(command="benchmark", benchmark_action="report")

    benchmark_compare = benchmark_sub.add_parser("compare", help="compare benchmark reports", parents=[common])
    benchmark_compare.add_argument("--baseline", required=True, help="baseline benchmark JSON")
    benchmark_compare.add_argument("--current", default=None, help="current benchmark JSON, or run a fresh benchmark")
    benchmark_compare.add_argument("--threshold", type=float, default=0.10, help="regression threshold")
    benchmark_compare.add_argument("--output", "-o", default=None, help="report output directory")
    benchmark_compare.set_defaults(command="benchmark", benchmark_action="compare")

    benchmark.set_defaults(command="benchmark", benchmark_action="run")

    return parser
