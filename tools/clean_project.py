# =====================================================
# NTPE 1.1 LTS Utility
# Clean Project Tool
# 放置位置：D:\Python\NTPE\tools\clean_project.py
# =====================================================

from __future__ import annotations

import argparse
import fnmatch
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

DEFAULT_CLEAN_DIRS = (
    "input",
    "output",
    "translated",
    "final_output",
    "translation_cache",
    "cache",
    "tmp",
    "logs",
    "sessions",
    "failed_chunks",
    ".ntpe_runtime_checkpoints",
)

DEFAULT_STATE_PATTERNS = (
    "translate_progress*.json",
    "resume*.json",
    "runtime_state*.json",
    "session_state*.json",
    "checkpoint*.json",
    "*.lock",
    "*.pid",
    "*.tmp",
)

PROTECTED_DIRS = {
    ".git",
    "adapters",
    "analysis",
    "benchmark",
    "cli",
    "compatibility",
    "config",
    "context",
    "core",
    "docs",
    "engine",
    "examples",
    "external_api",
    "gui",
    "integration",
    "lts",
    "memory",
    "packaging",
    "performance",
    "platform_services",
    "profiles",
    "prompt_packages",
    "regression",
    "release",
    "release_candidate",
    "reports",
    "rules",
    "runtime",
    "runtime_api",
    "schemas",
    "sdk",
    "stable_release",
    "tests",
    "tools",
    "translation",
    "web_ui",
    "workflow",
}

PROTECTED_FILE_PREFIXES = (
    "README",
    "CHANGELOG",
    "VERSION",
    "RELEASE",
    "Stable_Release",
    "Regression_",
    "Compatibility_",
    "Performance_",
    "Translation_",
    "Packaging_",
    "Release_",
    "RC_",
    "Beta_",
    "Build_",
)

PROTECTED_FILE_NAMES = {
    ".gitattributes",
    ".gitignore",
    "requirements.txt",
    "launcher.py",
    "ntpe_translate_txt.py",
}


@dataclass
class CleanResult:
    root: Path
    dry_run: bool
    cleaned_dirs: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    created_gitkeep: list[str] = field(default_factory=list)
    skipped_missing_dirs: list[str] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return len(self.cleaned_dirs) + len(self.deleted_files) + len(self.created_gitkeep)


def project_root_from(path: str | Path | None = None) -> Path:
    if path is None:
        return Path(__file__).resolve().parents[1]
    return Path(path).resolve()


def safe_relative(root: Path, target: Path) -> str:
    return target.resolve().relative_to(root.resolve()).as_posix()


def ensure_inside_project(root: Path, target: Path) -> None:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Refusing to clean outside project root: {target}") from exc


def remove_directory_contents(root: Path, directory: Path, *, dry_run: bool, result: CleanResult) -> None:
    ensure_inside_project(root, directory)
    if directory.name in PROTECTED_DIRS and directory.name not in DEFAULT_CLEAN_DIRS:
        raise ValueError(f"Refusing to clean protected directory: {directory}")

    if not directory.exists():
        if not dry_run:
            directory.mkdir(parents=True, exist_ok=True)
        result.skipped_missing_dirs.append(safe_relative(root, directory))
        if not dry_run:
            gitkeep = directory / ".gitkeep"
            gitkeep.write_text("", encoding="utf-8")
            result.created_gitkeep.append(safe_relative(root, gitkeep))
        return

    for child in directory.iterdir():
        ensure_inside_project(root, child)
        if child.name == ".gitkeep":
            continue
        if not dry_run:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    result.cleaned_dirs.append(safe_relative(root, directory))

    gitkeep = directory / ".gitkeep"
    if not dry_run:
        gitkeep.write_text("", encoding="utf-8")
    result.created_gitkeep.append(safe_relative(root, gitkeep))


def is_state_file(path: Path, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def is_protected_root_file(path: Path) -> bool:
    if path.name in PROTECTED_FILE_NAMES:
        return True
    return any(path.name.startswith(prefix) for prefix in PROTECTED_FILE_PREFIXES)


def remove_state_files(root: Path, patterns: Iterable[str], *, dry_run: bool, result: CleanResult) -> None:
    for path in root.iterdir():
        if not path.is_file():
            continue
        if not is_state_file(path, patterns):
            continue
        if is_protected_root_file(path):
            continue
        ensure_inside_project(root, path)
        result.deleted_files.append(safe_relative(root, path))
        if not dry_run:
            path.unlink()




def remove_python_caches(root: Path, *, dry_run: bool, result: CleanResult) -> None:
    for cache_dir in list(root.rglob("__pycache__")) + list(root.rglob(".pytest_cache")):
        ensure_inside_project(root, cache_dir)
        result.cleaned_dirs.append(safe_relative(root, cache_dir))
        if not dry_run and cache_dir.exists():
            shutil.rmtree(cache_dir)


def clean_project(
    root: str | Path | None = None,
    *,
    dry_run: bool = False,
    clean_dirs: Iterable[str] = DEFAULT_CLEAN_DIRS,
    state_patterns: Iterable[str] = DEFAULT_STATE_PATTERNS,
) -> CleanResult:
    project_root = project_root_from(root)
    if not project_root.exists():
        raise FileNotFoundError(f"Project root does not exist: {project_root}")
    if not (project_root / "requirements.txt").exists() and not (project_root / "launcher.py").exists():
        raise ValueError(f"Not an NTPE project root: {project_root}")

    result = CleanResult(root=project_root, dry_run=dry_run)
    for dirname in clean_dirs:
        remove_directory_contents(project_root, project_root / dirname, dry_run=dry_run, result=result)
    remove_state_files(project_root, state_patterns, dry_run=dry_run, result=result)
    remove_python_caches(project_root, dry_run=dry_run, result=result)
    return result


def format_report(result: CleanResult) -> str:
    lines = [
        "NTPE Project Cleaner",
        "====================",
        f"root: {result.root}",
        f"dry_run: {result.dry_run}",
        f"cleaned_dirs: {len(result.cleaned_dirs)}",
        f"deleted_files: {len(result.deleted_files)}",
        f"created_gitkeep: {len(result.created_gitkeep)}",
        "",
        "Cleaned directories:",
    ]
    if result.cleaned_dirs:
        lines.extend(f"- {item}" for item in result.cleaned_dirs)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Deleted state files:")
    if result.deleted_files:
        lines.extend(f"- {item}" for item in result.deleted_files)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean NTPE runtime artifacts before release packaging.")
    parser.add_argument("--root", default=None, help="NTPE project root. Defaults to parent of tools directory.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without deleting files.")
    parser.add_argument("--yes", action="store_true", help="Run without interactive confirmation.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root_from(args.root)

    if not args.yes and not args.dry_run:
        print("NTPE Project Cleaner")
        print("This will clear runtime folders such as input, output, translated, cache, logs, sessions, and checkpoints.")
        print("Source code, tests, configs, README, CHANGELOG, and Git files are preserved.")
        answer = input("Continue? (Y/N): ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled.")
            return 1

    result = clean_project(root, dry_run=args.dry_run)
    print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
