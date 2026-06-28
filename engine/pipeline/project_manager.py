from __future__ import annotations

from pathlib import Path

from core.project_profile import load_project_profile
from .session import PipelineSession


class ProjectManager:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def load_profile(self, profile_path: str | Path | None = None) -> dict:
        if profile_path is None:
            profile_path = self.root / "profiles" / "passion_profile.json"
        return load_project_profile(profile_path)

    def create_session(self, profile: dict) -> PipelineSession:
        project_id = profile["project"]["project_id"]
        return PipelineSession(root=self.root, project_id=project_id)

    def scan_normalized_files(self, profile: dict) -> list[Path]:
        normalized_dir = self.root / profile["paths"]["normalized_dir"]
        if not normalized_dir.exists():
            return []

        files = sorted(
            [p for p in normalized_dir.glob("*.txt") if p.is_file()],
            key=lambda p: p.name.lower(),
        )

        normalized = [p for p in files if p.stem.endswith("_normalized")]
        return normalized if normalized else files
