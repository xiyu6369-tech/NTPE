from __future__ import annotations

from pathlib import Path

from .project_manager import ProjectManager
from .stages import PipelineStages
from .utils import append_log, now_iso


class Pipeline:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.project_manager = ProjectManager(self.root)
        self.stages = PipelineStages(self.root)
        self.log_path = self.root / "logs" / "pipeline.log"

    def run_demo(self) -> dict:
        """
        v1.0 Core Demo Pipeline：
        1. 讀取 Project Profile
        2. 建立 Session
        3. 準備 demo chunk
        4. Prompt Builder 產生 Prompt Package
        5. Translation Engine 翻譯 Prompt Package

        這版先驗證 Pipeline 骨架，不直接批次翻整本。
        """
        started_at = now_iso()
        stage_results = []

        try:
            append_log(self.log_path, "Pipeline started")

            profile = self.project_manager.load_profile()
            session = self.project_manager.create_session(profile)
            session.set_status("running")

            append_log(self.log_path, f"Session created: {session.session_id}")

            # Stage 1
            session.set_stage("prepare_demo_chunk")
            r1 = self.stages.stage_prepare_demo_chunk(session, profile)
            session.add_stage_result(r1.to_dict())
            stage_results.append(r1.to_dict())
            append_log(self.log_path, f"{r1.stage}: {r1.status}")

            if r1.status != "success":
                session.set_status("failed")
                return self._failed(session, started_at, stage_results, r1.message)

            # Stage 2
            session.set_stage("build_prompt_package")
            r2 = self.stages.stage_build_prompt_package(session, profile, r1.data)
            session.add_stage_result(r2.to_dict())
            stage_results.append(r2.to_dict())
            append_log(self.log_path, f"{r2.stage}: {r2.status}")

            if r2.status != "success":
                session.set_status("failed")
                return self._failed(session, started_at, stage_results, r2.message)

            # Stage 3
            session.set_stage("translate_package")
            r3 = self.stages.stage_translate_package(session, profile, r2.data["package_path"])
            session.add_stage_result(r3.to_dict())
            stage_results.append(r3.to_dict())
            append_log(self.log_path, f"{r3.stage}: {r3.status}")

            if r3.status != "success":
                session.set_status("failed")
                return self._failed(session, started_at, stage_results, r3.message)

            session.set_status("success")
            append_log(self.log_path, f"Pipeline finished: {session.session_id}")

            return {
                "status": "success",
                "session_id": session.session_id,
                "started_at": started_at,
                "ended_at": now_iso(),
                "stages": stage_results,
                "session_path": str(session.path),
            }

        except Exception as e:
            append_log(self.log_path, f"Pipeline fatal error: {e}")
            return {
                "status": "failed",
                "started_at": started_at,
                "ended_at": now_iso(),
                "stages": stage_results,
                "error": str(e),
            }

    def _failed(self, session, started_at: str, stage_results: list[dict], error: str) -> dict:
        append_log(self.log_path, f"Pipeline failed: {error}")
        return {
            "status": "failed",
            "session_id": session.session_id,
            "started_at": started_at,
            "ended_at": now_iso(),
            "stages": stage_results,
            "session_path": str(session.path),
            "error": error,
        }
