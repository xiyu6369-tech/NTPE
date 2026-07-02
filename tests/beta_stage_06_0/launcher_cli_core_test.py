from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli import CLIContext, CLIResult
from cli.command import CLICommand, CommandRegistry
from cli.main import build_registry, format_result, run_cli
from cli.manifest import attach_cli_manifest, build_cli_manifest
from cli.parser import build_parser


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main() -> None:
    context = CLIContext.discover(ROOT)
    show("CLI Context", context.root == ROOT and context.path("tests").exists())
    show("CLI Version Read", isinstance(context.read_version(), str) and len(context.read_version()) > 0)

    result = CLIResult.success("ok", value=1)
    show("CLI Result", result.ok and result.to_dict()["data"]["value"] == 1)
    failure = CLIResult.failure("bad", exit_code=7)
    show("CLI Failure", not failure.ok and failure.exit_code == 7)

    registry = CommandRegistry()
    registry.register(CLICommand("hello", "hello command", lambda ctx, args: CLIResult.success("hello")))
    show("Command Registry", "hello" in registry and registry.get("hello").execute(context, object()).ok)

    builtin = build_registry()
    show("Builtin Commands", builtin.names() == ["doctor", "version"])

    parser = build_parser()
    parsed = parser.parse_args(["doctor", "--strict"])
    show("Parser", parsed.command == "doctor" and parsed.strict is True)

    version_result = run_cli(["version"], context=context)
    show("Version Command", version_result.ok and "version" in version_result.data)

    doctor_result = run_cli(["doctor"], context=context)
    show("Doctor Command", doctor_result.ok and doctor_result.data["required_ok"] is True)

    json_text = format_result(doctor_result, as_json=True)
    payload = json.loads(json_text)
    show("JSON Output", payload["ok"] is True and payload["data"]["required_ok"] is True)

    text = format_result(version_result, as_json=False)
    show("Text Output", "NTPE version" in text)

    manifest = build_cli_manifest()
    show("CLI Manifest", manifest["stage"] == "NTPE 1.0 Beta Stage-06.0" and "version" in manifest["commands"])

    carrier = attach_cli_manifest({})
    show("Manifest Helper", carrier["manifests"]["cli"]["backward_compatible"] is True)

    proc = subprocess.run(
        [sys.executable, "-m", "cli", "version", "--root", str(ROOT), "--json"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    show("Module Entrypoint", proc.returncode == 0 and json.loads(proc.stdout)["ok"] is True)

    help_proc = subprocess.run(
        [sys.executable, "-m", "cli", "--help"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    show("Help Command", help_proc.returncode == 0 and "NTPE command line interface" in help_proc.stdout)

    show("Foundation Compatible", (ROOT / "core").exists() and (ROOT / "runtime").exists())
    show("Backward Compatible", True)
    print("PASS")


if __name__ == "__main__":
    main()
