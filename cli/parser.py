from __future__ import annotations

import argparse


def _global_options() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--json", action="store_true", dest="as_json", help="print command result as JSON")
    parent.add_argument("--root", default=None, help="project root directory")
    return parent


def _add_translate(subparsers, common):
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


def _add_project(subparsers, common):
    project = subparsers.add_parser("project", help="manage NTPE translation projects", parents=[common])
    project_sub = project.add_subparsers(dest="project_action")

    project_create = project_sub.add_parser("create", help="create an NTPE project", parents=[common])
    project_create.add_argument("path", nargs="?", default=".", help="project directory")
    project_create.add_argument("--name", default=None, help="project display name")
    project_create.add_argument("--input", default="input", help="input directory name")
    project_create.add_argument("--output", default="output", help="output directory name")
    project_create.add_argument("--force", action="store_true", help="overwrite project metadata if it exists")
    project_create.set_defaults(command="project", project_action="create")

    project_open = project_sub.add_parser("open", help="open an NTPE project", parents=[common])
    project_open.add_argument("path", nargs="?", default=".", help="project directory")
    project_open.set_defaults(command="project", project_action="open")

    project_info = project_sub.add_parser("info", help="show project information", parents=[common])
    project_info.add_argument("path", nargs="?", default=".", help="project directory")
    project_info.set_defaults(command="project", project_action="info")

    project_validate = project_sub.add_parser("validate", help="validate project structure", parents=[common])
    project_validate.add_argument("path", nargs="?", default=".", help="project directory")
    project_validate.add_argument("--strict", action="store_true", help="fail on warnings")
    project_validate.set_defaults(command="project", project_action="validate")

    project_list = project_sub.add_parser("list", help="list projects under a directory", parents=[common])
    project_list.add_argument("path", nargs="?", default=".", help="directory to scan")
    project_list.set_defaults(command="project", project_action="list")

    project_export = project_sub.add_parser("export", help="export project metadata", parents=[common])
    project_export.add_argument("path", nargs="?", default=".", help="project directory")
    project_export.add_argument("--output", "-o", default=None, help="export file path")
    project_export.set_defaults(command="project", project_action="export")

    project_import = project_sub.add_parser("import", help="import project metadata", parents=[common])
    project_import.add_argument("package", help="project package JSON")
    project_import.add_argument("--output", "-o", default=".", help="target project directory")
    project_import.add_argument("--replace", action="store_true", help="replace existing metadata")
    project_import.set_defaults(command="project", project_action="import")

    project.set_defaults(command="project", project_action="info")


def _add_benchmark(subparsers, common):
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


def _add_quality(subparsers, common):
    quality = subparsers.add_parser("quality", help="check, score, repair, and report translation quality", parents=[common])
    quality_sub = quality.add_subparsers(dest="quality_action")

    def add_quality_io(parser):
        parser.add_argument("target", help="translated TXT file to inspect")
        parser.add_argument("--source", default=None, help="optional source TXT file")
        parser.add_argument("--glossary", default=None, help="glossary mapping file, JSON or source=target lines")
        parser.add_argument("--characters", default=None, help="character mapping file, JSON or source=target lines")
        parser.add_argument("--style", default="zh-TW", help="style profile")

    check = quality_sub.add_parser("check", help="run quality validation", parents=[common])
    add_quality_io(check)
    check.set_defaults(command="quality", quality_action="check")

    score = quality_sub.add_parser("score", help="score translation quality", parents=[common])
    add_quality_io(score)
    score.set_defaults(command="quality", quality_action="score")

    repair = quality_sub.add_parser("repair", help="repair common translation quality issues", parents=[common])
    add_quality_io(repair)
    repair.add_argument("--output", "-o", default=None, help="optional repaired output path")
    repair.set_defaults(command="quality", quality_action="repair")

    report = quality_sub.add_parser("report", help="write quality report", parents=[common])
    add_quality_io(report)
    report.add_argument("--output", "-o", default=None, help="optional report JSON output path")
    report.set_defaults(command="quality", quality_action="report")

    rules = quality_sub.add_parser("rules", help="list active quality rules", parents=[common])
    rules.add_argument("--style", default="zh-TW", help="style profile")
    rules.set_defaults(command="quality", quality_action="rules")

    quality.set_defaults(command="quality", quality_action="rules")


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

    _add_translate(subparsers, common)
    _add_project(subparsers, common)
    _add_benchmark(subparsers, common)
    _add_quality(subparsers, common)

    return parser
