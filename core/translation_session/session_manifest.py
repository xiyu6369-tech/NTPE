from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from core.translation_engine.utils import now_iso


@dataclass
class SessionManifest:
    session_id: str
    root: str
    runtime_version: str
    session_version: str = "1.2-professional-stage-05"
    compatibility_floor: str = "1.1-lts-stable"
    created_at: str = field(default_factory=now_iso)
    input_source: str = ""
    output_target: str = ""
    mode: str = "runtime"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def manifest_path(self) -> Path:
        return Path(self.root) / ".ntpe_sessions" / self.session_id / "session_manifest.json"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self) -> Path:
        from core.translation_engine.utils import save_json
        path = self.manifest_path
        path.parent.mkdir(parents=True, exist_ok=True)
        save_json(path, self.to_dict())
        return path
