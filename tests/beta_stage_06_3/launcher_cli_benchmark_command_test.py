from __future__ import annotations

import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.main import build_registry, run_cli
from cli.parser import build_parser
from cli.context import CLIContext
from cli.commands.benchmark import command_benchmark, command_benchmark_compare, command_benchmark_report
from cli.commands.manifest import build_benchmark_manifest


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main() -> None:
    root = Path.cwd()
    context = CLIContext.discover(root)

    parser = build_parser()
    args = parser.parse_args(["benchmark", "run", "--segments", "3", "--prompts", "2"])
    show("Benchmark Parser", args.command == "benchmark" and args.benchmark_action == "run")

    registry = build_registry()
    show("Benchmark Registered", "benchmark" in registry)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)

        result = run_cli(["benchmark", "run", "--segments", "3", "--prompts", "2", "--iterations", "1", "--output", str(out)], context=context)
        show("Benchmark Run", result.ok and result.data.get("summary", {}).get("total", 0) > 0)
        show("Benchmark JSON Export", (out / "benchmark.json").exists())
        show("Benchmark HTML Export", (out / "benchmark.html").exists())

        runtime = run_cli(["benchmark", "runtime", "--segments", "3", "--output", str(out)], context=context)
        show("Runtime Benchmark", runtime.ok and any(r["name"].startswith("runtime") for r in runtime.data["results"]))

        provider = run_cli(["benchmark", "provider", "--prompts", "2", "--output", str(out)], context=context)
        show("Provider Benchmark", provider.ok and provider.data.get("summary", {}).get("total", 0) > 0)

        stress = run_cli(["benchmark", "stress", "--segments", "3", "--iterations", "1", "--output", str(out)], context=context)
        show("Stress Benchmark", stress.ok and any("stress" in r["name"] or "soak" in r["name"] for r in stress.data["results"]))

        report = run_cli(["benchmark", "report", "--output", str(out), "--basename", "manual_report"], context=context)
        show("Benchmark Report", report.ok and (out / "manual_report.json").exists())

        baseline_path = out / "baseline.json"
        baseline = dict(result.data["report"])
        baseline_path.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")
        compare = run_cli(["benchmark", "compare", "--baseline", str(baseline_path), "--current", str(baseline_path), "--output", str(out)], context=context)
        show("Benchmark Compare", compare.ok and compare.data.get("regression", {}).get("status") == "PASS")

        show("Acceptance Benchmark", run_cli(["benchmark", "runtime", "--output", str(out)], context=context).ok)

    manifest = build_benchmark_manifest()
    show("Benchmark Manifest", manifest["component"] == "cli.benchmark" and "run" in manifest["subcommands"])

    show("CLI Manifest", run_cli([], context=context).ok and "benchmark" in run_cli([], context=context).data.get("commands", []))
    show("Backward Compatible", run_cli(["version"], context=context).ok and run_cli(["doctor"], context=context).ok)
    print("PASS")


if __name__ == "__main__":
    main()
