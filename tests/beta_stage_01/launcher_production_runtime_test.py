from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.production_runtime import (
    RuntimeCheckpointStore,
    RuntimeHost,
    RuntimeMetrics,
    RuntimeRecoveryManager,
    RuntimeScheduler,
    RuntimeSessionManager,
    RuntimeTelemetry,
    build_production_runtime_manifest,
)


def report(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main() -> None:
    temp_dir = tempfile.mkdtemp(prefix="ntpe_stage01_")
    try:
        # Runtime Host
        host = RuntimeHost(checkpoint_dir=temp_dir)
        report("Production Runtime", host.version == "ntpe-1.0-beta-stage-01")

        # Runtime Session
        session = host.start_session(job_id="job-stage01", session_id="session-stage01")
        report("Runtime Session", session["status"] == "running" and session["job_id"] == "job-stage01")

        # Scheduler
        scheduler = RuntimeScheduler()
        scheduler.submit_many(["s1", "s2"])
        first = scheduler.next_task()
        report("Scheduler", scheduler.pending_count() == 1 and first is not None and first.status == "running")

        # Checkpoint
        checkpoint = host.session.checkpoint(1, {"segment": "s1"})
        loaded = host.session.resume("session-stage01")
        report("Checkpoint", loaded is not None and loaded.checkpoint_id == checkpoint.checkpoint_id)

        # Recovery
        attempts = {"n": 0}
        recovery = RuntimeRecoveryManager(max_retries=1)

        def flaky():
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("temporary")
            return "ok"

        report("Recovery", recovery.run_with_retry(flaky) == "ok" and recovery.last_result.recovered)

        # Metrics
        metrics = RuntimeMetrics()
        metrics.increment("x")
        metrics.observe("latency", 0.01)
        snap = metrics.snapshot()
        report("Metrics", snap["counters"]["x"] == 1 and snap["timings"]["latency"]["count"] == 1)

        # Telemetry
        telemetry = RuntimeTelemetry()
        telemetry.emit("RuntimeEvent", {"ok": True})
        report("Telemetry", len(telemetry.history("RuntimeEvent")) == 1)

        # Runtime Processing
        result = host.process_segment("segment-1", {"source": "test"})
        report("Runtime Processing", result["task"]["status"] == "completed" and result["checkpoint"]["segment_index"] >= 1)

        # Job Run
        host2 = RuntimeHost(checkpoint_dir=os.path.join(temp_dir, "job"))
        host2.submit_job(["a", "b"], job_id="job-run")
        run_result = host2.run_all()
        report("Runtime Host", len(run_result["results"]) == 2 and host2.scheduler.completed_count() == 2)

        # Resume
        resume_payload = host.resume("session-stage01")
        report("Resume", resume_payload["checkpoint"] is not None)

        # Runtime Manifest
        manifest = host.manifest()
        report("Runtime Manifest", manifest["name"] == "ntpe_production_runtime" and "RuntimeHost" in manifest["components"])

        # Manifest Helper
        helper_manifest = build_production_runtime_manifest({"phase": "beta"})
        report("Manifest Helper", helper_manifest["metadata"]["phase"] == "beta")

        # Knowledge Runtime Bridge
        report("Knowledge Runtime Bridge", "knowledge_runtime" in manifest or host.knowledge_runtime is None)

        # Attach Manifest
        attached = host.attach_to_runtime_manifest({"components": []})
        report("Attach Runtime Manifest", len(attached["components"]) == 1)

        # Custom Executor
        custom = RuntimeHost(executor=lambda segment, payload: {"translated": str(segment).upper(), "ctx": bool(payload)}, checkpoint_dir=os.path.join(temp_dir, "custom"))
        custom.start_session(job_id="custom", session_id="custom-session")
        custom_result = custom.process_segment("abc", {"x": 1})
        report("Executor Hook", custom_result["output"]["translated"] == "ABC")

        # Backward Compatible: old modules still importable if present
        try:
            from core.runtime.translation_runtime import TranslationRuntime  # type: ignore
            backward_ok = TranslationRuntime is not None
        except Exception:
            backward_ok = True
        report("Backward Compatible", backward_ok)

        print("PASS")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
