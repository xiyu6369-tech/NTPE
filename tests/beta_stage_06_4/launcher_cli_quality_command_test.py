from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.main import build_registry, run_cli
from cli.parser import build_parser
from cli.commands.manifest import build_quality_manifest


def check(name: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{name:<35} {status}")
    if not condition:
        raise AssertionError(name)


def make_workspace() -> Path:
    root = Path(tempfile.mkdtemp(prefix="ntpe_cli_quality_"))
    (root / "core").mkdir()
    (root / "runtime").mkdir()
    (root / "translation").mkdir()
    (root / "translated.txt").write_text('這是測試翻譯。\n鄭泰義說：「你好。」', encoding="utf-8")
    (root / "source.txt").write_text('정태의가 말했다.', encoding="utf-8")
    (root / "glossary.txt").write_text('정태의=鄭泰義\n', encoding="utf-8")
    (root / "bad.txt").write_text('这是测试。\n정태의\n정태의\n정태의', encoding="utf-8")
    (root / "empty.txt").write_text('', encoding="utf-8")
    return root


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(["quality", "check", "translated.txt"])
    check("Quality Parser", args.command == "quality" and args.quality_action == "check")

    registry = build_registry()
    check("Quality Registered", "quality" in registry.names())

    root = make_workspace()
    try:
        target = str(root / "translated.txt")
        source = str(root / "source.txt")
        glossary = str(root / "glossary.txt")

        result = run_cli(["--root", str(root), "quality", "check", target, "--source", source, "--glossary", glossary])
        check("Quality Check", result.exit_code == 0 and "score" in result.data)

        result = run_cli(["--root", str(root), "quality", "score", target, "--source", source, "--glossary", glossary])
        check("Quality Score", result.exit_code == 0 and 0 <= result.data.get("score", -1) <= 1)

        repaired = root / "repaired.txt"
        result = run_cli(["--root", str(root), "quality", "repair", str(root / "bad.txt"), "--output", str(repaired), "--glossary", glossary])
        check("Quality Repair", result.exit_code == 0 and repaired.exists())

        report = root / "quality_report.json"
        result = run_cli(["--root", str(root), "quality", "report", target, "--source", source, "--output", str(report)])
        data = json.loads(report.read_text(encoding="utf-8"))
        check("Quality Report", result.exit_code == 0 and report.exists() and "score" in data)

        result = run_cli(["--root", str(root), "quality", "rules"])
        check("Quality Rules", result.exit_code == 0 and "semantic" in result.data.get("rules", []))

        json_result = run_cli(["--root", str(root), "quality", "score", target])
        check("JSON Compatible Result", json_result.to_dict()["ok"] is True)

        manifest = build_quality_manifest()
        check("Quality Manifest", manifest["version"] == "1.0-beta-stage-06.4" and "quality" in manifest["commands"])

        result = run_cli(["--root", str(root), "quality", "rules", "--json"])
        check("CLI Manifest", result.exit_code == 0 and "cli_quality" in result.data.get("manifests", {}))

        result = run_cli(["--root", str(root), "quality", "check", str(root / "empty.txt"), "--source", source])
        check("Acceptance Quality", result.exit_code != 0 and result.errors)

        version_result = run_cli(["--root", str(root), "version"])
        translate_present = "translate" in build_registry().names()
        check("Backward Compatible", version_result.exit_code == 0 and translate_present)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("PASS")


if __name__ == "__main__":
    main()
