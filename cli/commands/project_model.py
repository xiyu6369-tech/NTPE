from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_FILE = "ntpe_project.json"
PROJECT_DIRS = ["input", "output", "sessions", "reports", "knowledge", "benchmark_reports", "quality_reports"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ProjectMetadata:
    name: str
    root: str
    version: str = "1.0-beta-stage-06.2"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    input_dir: str = "input"
    output_dir: str = "output"
    session_dir: str = "sessions"
    report_dir: str = "reports"
    provider: str = "mock"
    quality: str = "standard"
    capabilities: List[str] = field(default_factory=lambda: [
        "translation",
        "session",
        "knowledge",
        "benchmark",
        "quality",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root": self.root,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "session_dir": self.session_dir,
            "report_dir": self.report_dir,
            "provider": self.provider,
            "quality": self.quality,
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectMetadata":
        return cls(
            name=str(data.get("name") or "NTPE Project"),
            root=str(data.get("root") or "."),
            version=str(data.get("version") or "1.0-beta-stage-06.2"),
            created_at=str(data.get("created_at") or utc_now()),
            updated_at=str(data.get("updated_at") or utc_now()),
            input_dir=str(data.get("input_dir") or "input"),
            output_dir=str(data.get("output_dir") or "output"),
            session_dir=str(data.get("session_dir") or "sessions"),
            report_dir=str(data.get("report_dir") or "reports"),
            provider=str(data.get("provider") or "mock"),
            quality=str(data.get("quality") or "standard"),
            capabilities=list(data.get("capabilities") or []),
        )


def project_file(root: Path) -> Path:
    return root / PROJECT_FILE


def read_project(root: Path) -> ProjectMetadata:
    path = project_file(root)
    if not path.exists():
        raise FileNotFoundError(f"NTPE project metadata not found: {path}")
    return ProjectMetadata.from_dict(json.loads(path.read_text(encoding="utf-8")))


def write_project(root: Path, metadata: ProjectMetadata) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = project_file(root)
    path.write_text(json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


@dataclass
class ProjectValidation:
    root: Path
    exists: bool
    metadata_exists: bool
    missing_dirs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exists and self.metadata_exists and not self.missing_dirs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": str(self.root),
            "exists": self.exists,
            "metadata_exists": self.metadata_exists,
            "missing_dirs": list(self.missing_dirs),
            "warnings": list(self.warnings),
            "ok": self.ok,
        }
