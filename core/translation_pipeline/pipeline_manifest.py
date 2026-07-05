from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .pipeline_step import PipelineStep


@dataclass(frozen=True)
class PipelineManifest:
    """Stable manifest for the official NTPE 1.2 Professional pipeline."""

    pipeline_id: str
    pipeline_version: str
    compatibility_floor: str
    steps: tuple[PipelineStep, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target
