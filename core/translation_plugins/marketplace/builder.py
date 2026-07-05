from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import MarketplacePluginManifest
from .package import MarketplacePluginPackage

_EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True)
class PluginPackageBuilder:
    """Builds deterministic NTPE plugin distribution packages.

    The builder owns packaging only. It does not install, enable, execute, or
    register plugins. Those responsibilities remain in installer / registry /
    runtime layers to preserve marketplace boundaries.
    """

    source_dir: Path
    output_dir: Path
    ntpe_version: str = "1.2.0"

    @classmethod
    def create(cls, source_dir: str | Path, output_dir: str | Path, ntpe_version: str = "1.2.0") -> "PluginPackageBuilder":
        return cls(source_dir=Path(source_dir), output_dir=Path(output_dir), ntpe_version=ntpe_version)

    @property
    def manifest_path(self) -> Path:
        return self.source_dir / "plugin_manifest.json"

    def load_manifest(self) -> MarketplacePluginManifest:
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return MarketplacePluginManifest.from_dict(data)

    def validate_source(self) -> dict[str, Any]:
        errors: list[str] = []
        if not self.source_dir.exists():
            errors.append("source_dir does not exist")
        if not self.source_dir.is_dir():
            errors.append("source_dir must be a directory")
        if not self.manifest_path.exists():
            errors.append("plugin_manifest.json is required")
        if errors:
            return {"status": "failed", "errors": errors}

        package = MarketplacePluginPackage.load(self.source_dir)
        validation = package.validate(ntpe_version=self.ntpe_version)
        errors.extend(validation.get("errors", []))
        entrypoint = package.manifest.entrypoint
        if entrypoint and ":" in entrypoint:
            module_name = entrypoint.split(":", 1)[0].replace(".", "/") + ".py"
            if not (self.source_dir / module_name).exists():
                errors.append(f"entrypoint module not found: {module_name}")
        return {
            "status": "success" if not errors else "failed",
            "plugin_id": package.manifest.plugin_id,
            "errors": errors,
        }

    def iter_package_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.source_dir.rglob("*"):
            if path.is_dir():
                continue
            relative = path.relative_to(self.source_dir)
            if any(part in _EXCLUDED_DIRS for part in relative.parts):
                continue
            if path.suffix in _EXCLUDED_SUFFIXES:
                continue
            files.append(path)
        return sorted(files, key=lambda item: str(item.relative_to(self.source_dir)).replace("\\", "/"))

    def build(self, replace: bool = False) -> dict[str, Any]:
        validation = self.validate_source()
        if validation["status"] != "success":
            return validation

        manifest = self.load_manifest()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        package_name = f"{manifest.plugin_id}-{manifest.version}.ntpe-plugin.zip"
        package_path = self.output_dir / package_name
        if package_path.exists() and not replace:
            return {"status": "failed", "plugin_id": manifest.plugin_id, "error": "package already exists", "package_path": str(package_path)}

        with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in self.iter_package_files():
                archive.write(file, arcname=str(file.relative_to(self.source_dir)).replace("\\", "/"))

        digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
        metadata = {
            "schema": "ntpe.plugin.package.v1",
            "plugin_id": manifest.plugin_id,
            "version": manifest.version,
            "package": package_path.name,
            "sha256": digest,
            "file_count": len(self.iter_package_files()),
        }
        metadata_path = package_path.with_suffix(package_path.suffix + ".json")
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "success",
            "plugin_id": manifest.plugin_id,
            "version": manifest.version,
            "package_path": str(package_path),
            "metadata_path": str(metadata_path),
            "sha256": digest,
            "file_count": metadata["file_count"],
        }

    def stage_directory(self, stage_root: str | Path, replace: bool = False) -> dict[str, Any]:
        validation = self.validate_source()
        if validation["status"] != "success":
            return validation
        manifest = self.load_manifest()
        target = Path(stage_root) / manifest.plugin_id
        if target.exists() and not replace:
            return {"status": "failed", "plugin_id": manifest.plugin_id, "error": "stage target already exists"}
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.source_dir, target, ignore=shutil.ignore_patterns(*_EXCLUDED_DIRS, "*.pyc", "*.pyo"))
        return {"status": "success", "plugin_id": manifest.plugin_id, "stage_path": str(target)}
