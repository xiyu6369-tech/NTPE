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
from cli.commands.manifest import build_session_manifest
from cli.commands.session_store import CLISessionStore


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="ntpe_cli_session_"))
    try:
        (tmp / "core").mkdir()
        (tmp / "runtime").mkdir()
        (tmp / "translation").mkdir()
        context = CLIContext(root=tmp)

        parser = build_parser()
        parsed = parser.parse_args(["session", "list"])
        check("Session Parser", parsed.command == "session" and parsed.session_action == "list")

        registry = build_registry()
        check("Session Registered", "session" in registry.names())

        store = CLISessionStore(tmp)
        record = store.create(session_id="session-test", job_id="job-test")
        check("Session Store Create", record.session_id == "session-test")

        result_create = run_cli(["--root", str(tmp), "session", "create", "session-cli", "--job-id", "job-cli"], context=context)
        check("Session Create", result_create.ok and result_create.data["session"]["session_id"] == "session-cli")

        result_list = run_cli(["--root", str(tmp), "session", "list"], context=context)
        check("Session List", result_list.ok and result_list.data["count"] >= 2)

        result_info = run_cli(["--root", str(tmp), "session", "info", "session-cli"], context=context)
        check("Session Info", result_info.ok and result_info.data["session"]["job_id"] == "job-cli")

        result_pause = run_cli(["--root", str(tmp), "session", "pause", "session-cli"], context=context)
        check("Session Pause", result_pause.ok and result_pause.data["session"]["status"] == "paused")

        result_resume = run_cli(["--root", str(tmp), "session", "resume", "session-cli"], context=context)
        check("Session Resume", result_resume.ok and result_resume.data["session"]["status"] == "running")

        state = json.dumps({"chunk": 3, "status": "ok"})
        result_checkpoint = run_cli(["--root", str(tmp), "session", "checkpoint", "session-cli", "--segment", "3", "--state-json", state], context=context)
        check("Checkpoint", result_checkpoint.ok and result_checkpoint.data["checkpoint"]["segment_index"] == 3)

        result_restore = run_cli(["--root", str(tmp), "session", "restore", "session-cli"], context=context)
        check("Restore", result_restore.ok and result_restore.data["checkpoint"]["state"]["chunk"] == 3)

        result_stop = run_cli(["--root", str(tmp), "session", "stop", "session-cli"], context=context)
        check("Session Stop", result_stop.ok and result_stop.data["session"]["status"] == "stopped")

        result_cleanup = run_cli(["--root", str(tmp), "session", "cleanup", "--status", "stopped"], context=context)
        check("Cleanup", result_cleanup.ok and "session-cli" in result_cleanup.data["deleted"])

        result_json = run_cli(["--root", str(tmp), "session", "demo"], context=context)
        check("JSON Compatible Result", result_json.to_dict()["ok"] is True)

        manifest = build_session_manifest()
        check("Session Manifest", manifest["version"] == "1.0-beta-stage-06.5" and "checkpoint" in manifest["subcommands"])

        result_cli = run_cli(["--root", str(tmp)], context=context)
        check("CLI Manifest", result_cli.ok and "session" in result_cli.data["commands"])

        acceptance = run_cli(["--root", str(tmp), "session", "list"], context=context)
        check("Acceptance Session", acceptance.ok)

        check("Backward Compatible", run_cli(["--root", str(tmp), "version"], context=context).ok)

        print("PASS")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
