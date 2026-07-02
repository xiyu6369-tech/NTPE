from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .project_model import PROJECT_DIRS, PROJECT_FILE, ProjectMetadata, ProjectValidation, read_project, utc_now, write_project


class ProjectManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, path: str | Path) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        return p.resolve()

    def create(
        self,
        path: str | Path = ".",
        name: Optional[str] = None,
        input_dir: str = "input",
        output_dir: str = "output",
        force: bool = False,
    ) -> Dict[str, Any]:
        project_root = self.resolve(path)
        meta_path = project_root / PROJECT_FILE
        if meta_path.exists() and not force:
            raise FileExistsError(f"NTPE project already exists: {meta_path}")
        for folder in set(PROJECT_DIRS + [input_dir, output_dir]):
            (project_root / folder).mkdir(parents=True, exist_ok=True)
        metadata = ProjectMetadata(
            name=name or project_root.name or "NTPE Project",
            root=str(project_root),
            input_dir=input_dir,
            output_dir=output_dir,
        )
        write_project(project_root, metadata)
        return {"project": metadata.to_dict(), "metadata_path": str(meta_path)}

    def open(self, path: str | Path = ".") -> Dict[str, Any]:
        project_root = self.resolve(path)
        metadata = read_project(project_root)
        return {"project": metadata.to_dict(), "metadata_path": str(project_root / PROJECT_FILE)}

    def info(self, path: str | Path = ".") -> Dict[str, Any]:
        data = self.open(path)
        project_root = Path(data["project"]["root"])
        data["directories"] = {
            "input": str(project_root / data["project"].get("input_dir", "input")),
            "output": str(project_root / data["project"].get("output_dir", "output")),
            "sessions": str(project_root / data["project"].get("session_dir", "sessions")),
            "reports": str(project_root / data["project"].get("report_dir", "reports")),
        }
        return data

    def validate(self, path: str | Path = ".") -> ProjectValidation:
        project_root = self.resolve(path)
        exists = project_root.exists() and project_root.is_dir()
        metadata_exists = (project_root / PROJECT_FILE).exists()
        missing_dirs: List[str] = []
        warnings: List[str] = []
        if exists:
            for folder in PROJECT_DIRS:
                if not (project_root / folder).exists():
                    missing_dirs.append(folder)
        else:
            warnings.append("project root does not exist")
        if not metadata_exists:
            warnings.append("project metadata missing")
        return ProjectValidation(project_root, exists, metadata_exists, missing_dirs, warnings)

    def list(self, path: str | Path = ".") -> Dict[str, Any]:
        base = self.resolve(path)
        projects: List[Dict[str, Any]] = []
        if base.exists():
            candidates = [base] + [p for p in base.iterdir() if p.is_dir()]
            for candidate in candidates:
                meta = candidate / PROJECT_FILE
                if meta.exists():
                    try:
                        projects.append(read_project(candidate).to_dict())
                    except Exception:
                        projects.append({"root": str(candidate), "error": "invalid project metadata"})
        return {"root": str(base), "count": len(projects), "projects": projects}

    def export(self, path: str | Path = ".", output: Optional[str | Path] = None) -> Dict[str, Any]:
        project_root = self.resolve(path)
        metadata = read_project(project_root)
        validation = self.validate(project_root).to_dict()
        package = {
            "package_type": "ntpe.project",
            "version": "1.0-beta-stage-06.2",
            "exported_at": utc_now(),
            "project": metadata.to_dict(),
            "validation": validation,
        }
        if output:
            out = self.resolve(output)
        else:
            out = project_root / "reports" / "ntpe_project_export.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"package": package, "output": str(out)}

    def import_package(self, package: str | Path, output: str | Path = ".", replace: bool = False) -> Dict[str, Any]:
        package_path = self.resolve(package)
        data = json.loads(package_path.read_text(encoding="utf-8"))
        if data.get("package_type") != "ntpe.project":
            raise ValueError("invalid NTPE project package")
        target = self.resolve(output)
        meta_path = target / PROJECT_FILE
        if meta_path.exists() and not replace:
            raise FileExistsError(f"NTPE project already exists: {meta_path}")
        project_data = dict(data.get("project") or {})
        project_data["root"] = str(target)
        project_data["updated_at"] = utc_now()
        metadata = ProjectMetadata.from_dict(project_data)
        for folder in PROJECT_DIRS:
            (target / folder).mkdir(parents=True, exist_ok=True)
        write_project(target, metadata)
        return {"project": metadata.to_dict(), "metadata_path": str(meta_path), "source_package": str(package_path)}
