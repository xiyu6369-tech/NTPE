from __future__ import annotations

from pathlib import Path

from .utils import now_iso, save_json, load_json


class PipelineSession:
    def __init__(self, root: str | Path, project_id: str):
        self.root = Path(root)
        self.project_id = project_id
        self.session_id = f"SESSION_{project_id.upper()}_{now_iso().replace(':', '').replace('-', '').replace('T', '_')}"
        self.path = self.root / "sessions" / f"{self.session_id}.json"

        self.data = {
            "session_id": self.session_id,
            "project_id": project_id,
            "status": "created",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "current_stage": "",
            "stages": [],
            "files": [],
            "chunks": [],
            "notes": [],
        }

    @classmethod
    def load(cls, root: str | Path, path: str | Path):
        path = Path(path)
        data = load_json(path)
        obj = cls(root=root, project_id=data.get("project_id", "unknown"))
        obj.session_id = data["session_id"]
        obj.path = path
        obj.data = data
        return obj

    def set_status(self, status: str) -> None:
        self.data["status"] = status
        self.data["updated_at"] = now_iso()
        self.save()

    def set_stage(self, stage: str) -> None:
        self.data["current_stage"] = stage
        self.data["updated_at"] = now_iso()
        self.save()

    def add_stage_result(self, result: dict) -> None:
        self.data["stages"].append(result)
        self.data["updated_at"] = now_iso()
        self.save()

    def add_note(self, note: str) -> None:
        self.data["notes"].append({
            "at": now_iso(),
            "note": note,
        })
        self.save()

    def save(self) -> None:
        save_json(self.path, self.data)
