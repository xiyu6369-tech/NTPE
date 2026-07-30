from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSchedulerResumeContract, RuntimeSchedulerStateBridge


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_complete_snapshot_builds_already_complete_plan() -> None:
    bridge = RuntimeSchedulerStateBridge()
    contract = RuntimeSchedulerResumeContract()
    snapshot = bridge.build_scheduler_snapshot(
        {
            "runtime_id": "runtime-complete-325",
            "chunks": [
                {"chunk_index": 1, "status": "done"},
                {"chunk_index": 2, "status": "done"},
            ],
        }
    )
    plan = contract.build_resume_plan(snapshot)

    assert plan["runtime_id"] == "runtime-complete-325"
    assert plan["chunks_total"] == 2
    assert plan["resume_chunks"] == []
    assert plan["skip_chunks"] == [1, 2]
    assert plan["failed_chunks"] == []
    assert plan["merge_ready"] is True
    assert plan["resumable"] is False
    assert plan["reason"] == "already_complete"
    assert contract.validate_resume_plan(plan)["valid"] is True


def test_partial_failed_and_missing_snapshots_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    try:
        contract = RuntimeSchedulerResumeContract()

        partial = contract.build_resume_plan(
            {
                "runtime_id": "runtime-partial-325",
                "chunks_total": 4,
                "pending_chunks": [2, 4],
                "done_chunks": [1],
                "failed_chunks": [3],
                "merge_ready": False,
                "metadata": {"source": "root-test"},
            }
        )
        failed_runtime_snapshot = contract.build_resume_plan(
            {
                "runtime_id": "runtime-failed-325",
                "collector_manifest": {"chunks_total": 3, "done_chunks": [1], "missing_chunks": [2], "failed_chunks": [3]},
                "failed_chunk_report": [{"chunk_index": 3, "error": "schema error"}],
                "merge_ready": False,
            }
        )
        defaults = contract.build_resume_plan({})

        assert partial["resume_chunks"] == [2, 3, 4]
        assert partial["skip_chunks"] == [1]
        assert partial["failed_chunks"] == [3]
        assert partial["resumable"] is True
        assert partial["reason"] == "resume_required"
        assert partial["metadata"]["source"] == "root-test"
        assert contract.validate_resume_plan(partial)["valid"] is True

        assert failed_runtime_snapshot["chunks_total"] == 3
        assert failed_runtime_snapshot["resume_chunks"] == [2, 3]
        assert failed_runtime_snapshot["failed_chunks"] == [3]
        assert failed_runtime_snapshot["resumable"] is True
        assert contract.validate_resume_plan(failed_runtime_snapshot)["valid"] is True

        assert defaults["runtime_id"] == "runtime-state-unknown"
        assert defaults["chunks_total"] == 0
        assert defaults["resumable"] is False
        assert defaults["reason"] == "no_chunks"
        assert contract.validate_resume_plan(defaults)["valid"] is True

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert "core.translation_engine.provider_runtime" not in sys.modules
        assert "core.production_runtime" not in sys.modules
        assert "requests" not in sys.modules
        assert "httpx" not in sys.modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_complete_snapshot_builds_already_complete_plan()
    test_partial_failed_and_missing_snapshots_without_runtime_dependencies()
    print("NTPE TE-v3.2 Stage-3.2.5 Runtime Scheduler Resume Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
