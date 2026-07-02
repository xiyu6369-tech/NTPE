from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.context import CLIContext
from cli.main import build_registry, run_cli
from cli.parser import build_parser
from cli.commands.manifest import build_translate_manifest
from cli.commands.translate_options import TranslateOptions
from cli.commands.translate_progress import TranslateProgress
from cli.commands.translate_report import TranslateReport
from cli.commands.translate_runner import TranslateRunner


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def make_project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="ntpe_cli_translate_"))
    for folder in ["core", "runtime", "translation", "benchmark", "tests", "config", "cli"]:
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "VERSION.txt").write_text("1.0.0-beta", encoding="utf-8")
    return root


def main() -> None:
    root = make_project()
    try:
        ctx = CLIContext.discover(root)
        src = root / "novel.txt"
        src.write_text("안녕하세요", encoding="utf-8")
        folder = root / "input"
        folder.mkdir()
        (folder / "a.txt").write_text("A", encoding="utf-8")
        (folder / "b.txt").write_text("B", encoding="utf-8")

        parser = build_parser()
        parsed = parser.parse_args(["translate", str(src), "--output", str(root / "out")])
        check("Translate Parser", parsed.command == "translate" and parsed.input == str(src))

        registry = build_registry()
        check("Translate Registered", "translate" in registry.names())

        options = TranslateOptions.from_args(parsed)
        check("Translate Options", options.input_path == src and options.output_path == root / "out")

        progress = TranslateProgress(total=1)
        progress.add_completed("a", "b")
        check("Translate Progress", progress.completed == 1 and progress.ok)

        report = TranslateReport(provider="mock", quality="standard")
        report.add(status="completed", source="a", output="b")
        check("Translate Report", report.to_dict()["total"] == 1)

        runner = TranslateRunner(ctx)
        sources = runner.discover_sources(options)
        check("Source Discovery File", sources == [src])

        result = runner.run(options)
        output_file = root / "out" / "novel_zh.txt"
        check("Translate File", output_file.exists() and result.progress.completed == 1)

        folder_result = run_cli(["--root", str(root), "translate", str(folder), "--output", str(root / "out_folder")])
        check("Translate Folder", folder_result.ok and folder_result.data["progress"]["completed"] == 2)

        resume_result = run_cli(["--root", str(root), "translate", str(folder), "--output", str(root / "out_folder"), "--resume"])
        check("Resume Translation", resume_result.ok and resume_result.data["progress"]["skipped"] == 2)

        provider_result = run_cli(["--root", str(root), "translate", str(src), "--output", str(root / "out_provider"), "--provider", "nvidia"])
        check("Provider Option", provider_result.ok and provider_result.data["report"]["provider"] == "nvidia")

        quality_result = run_cli(["--root", str(root), "translate", str(src), "--output", str(root / "out_quality"), "--quality", "high"])
        check("Quality Option", quality_result.ok and quality_result.data["report"]["quality"] == "high")

        dry_result = run_cli(["--root", str(root), "translate", str(src), "--output", str(root / "dry"), "--dry-run"])
        check("Dry Run", dry_result.ok and not (root / "dry" / "novel_zh.txt").exists())

        json_result = run_cli(["--root", str(root), "--json", "translate", str(src), "--output", str(root / "out_json")])
        check("JSON Compatible Result", json_result.ok and "progress" in json_result.data)

        custom_ctx = CLIContext.discover(root)
        custom_ctx.metadata["translation_hook"] = lambda text, opts: "HOOK:" + text
        hook_result = run_cli(["translate", str(src), "--output", str(root / "hook")], context=custom_ctx)
        hook_output = root / "hook" / "novel_zh.txt"
        check("Translation Hook", hook_result.ok and hook_output.read_text(encoding="utf-8").startswith("HOOK:"))

        check("Progress Report", (root / "out_folder" / "translation_report.json").exists())

        manifest = build_translate_manifest()
        check("Translate Manifest", manifest["version"] == "1.0-beta-stage-06.1")

        check("CLI Manifest", "cli_translate" in provider_result.data.get("manifests", {}))
        check("Acceptance Translate", run_cli(["--root", str(root), "translate", str(src), "--output", str(root / "accept")]).ok)
        check("Backward Compatible", run_cli(["--root", str(root), "version"]).ok and run_cli(["--root", str(root), "doctor"]).ok)

        print("PASS")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
