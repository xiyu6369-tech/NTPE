# =====================================================
# NTPE Project Cleanup Tool
# Stage-10.6 Project Cleanup and Archive Policy
# Safe mode: remove generated files; archive root release history.
# =====================================================

from __future__ import annotations

import json
import shutil
from pathlib import Path

KEEP_ROOT = {
    ".gitignore",
    ".gitattributes",
    "README.md",
    "CHANGELOG.md",
    "VERSION.txt",
    "launcher.py",
    "launcher_translate.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
}

ARCHIVE_PREFIXES = (
    "README_",
    "CHANGELOG_",
    "RELEASE_NOTES_",
    "LTS_",
    "NTPE_1_1_",
    "NTPE_1_2_",
    "Compatibility_",
    "Performance_",
    "Regression_",
    "Release_",
    "RC_",
    "Packaging_",
    "Distribution_",
    "Build_",
    "Beta_",
    "Clean_Project_",
    "Stable_",
    "Translation_",
)

ARCHIVE_SUFFIXES = (
    "_Report.md",
    "_Manifest.json",
    "_Hash.json",
    "_Validation.json",
)


def remove_generated(root: Path) -> list[str]:
    removed: list[str] = []
    for file in list(root.rglob("*.pyc")):
        removed.append(str(file.relative_to(root)))
        file.unlink(missing_ok=True)
    for cache_dir in sorted(root.rglob("__pycache__"), key=lambda p: len(p.parts), reverse=True):
        removed.append(str(cache_dir.relative_to(root)) + "/")
        shutil.rmtree(cache_dir, ignore_errors=True)
    for name in (".pytest_cache", ".mypy_cache"):
        for cache_dir in sorted(root.rglob(name), key=lambda p: len(p.parts), reverse=True):
            removed.append(str(cache_dir.relative_to(root)) + "/")
            shutil.rmtree(cache_dir, ignore_errors=True)
    return removed


def archive_root_history(root: Path) -> list[dict[str, str]]:
    archive = root / "docs" / "archive" / "release_history"
    archive.mkdir(parents=True, exist_ok=True)
    moved: list[dict[str, str]] = []
    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.name in KEEP_ROOT:
            continue
        if path.suffix.lower() not in {".md", ".txt", ".json"}:
            continue
        name = path.name
        should_archive = name in {"README.txt", "README_UPDATE.txt"}
        should_archive = should_archive or name.startswith(ARCHIVE_PREFIXES)
        should_archive = should_archive or name.endswith(ARCHIVE_SUFFIXES)
        if not should_archive:
            continue
        dest = archive / name
        if dest.exists():
            stem, suffix = dest.stem, dest.suffix
            index = 1
            while dest.exists():
                dest = archive / f"{stem}_{index}{suffix}"
                index += 1
        shutil.move(str(path), str(dest))
        moved.append({"from": str(path.relative_to(root)), "to": str(dest.relative_to(root))})
    return moved


def remove_empty_dirs(root: Path) -> list[str]:
    removed: list[str] = []
    dirs = [p for p in root.rglob("*") if p.is_dir() and ".git" not in p.parts]
    for directory in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        try:
            next(directory.iterdir())
        except StopIteration:
            removed.append(str(directory.relative_to(root)) + "/")
            directory.rmdir()
    return removed


def run_cleanup(root: Path | None = None) -> dict[str, object]:
    root = (root or Path.cwd()).resolve()
    removed_generated = remove_generated(root)
    archived = archive_root_history(root)
    removed_empty = remove_empty_dirs(root)
    report = {
        "stage": "NTPE 1.2 Professional Stage-10.6 Project Cleanup and Archive Policy",
        "status": "success",
        "root": str(root),
        "removed_generated_count": len(removed_generated),
        "removed_generated": removed_generated,
        "archived_root_documents_count": len(archived),
        "archived_root_documents": archived,
        "removed_empty_directories_count": len(removed_empty),
        "removed_empty_directories": removed_empty,
    }
    report_dir = root / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "STAGE_10_6_PROJECT_CLEANUP_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    result = run_cleanup()
    print("NTPE Project Cleanup Tool")
    print("=========================")
    print(f"status: {result['status']}")
    print(f"removed_generated: {result['removed_generated_count']}")
    print(f"archived_root_documents: {result['archived_root_documents_count']}")
    print(f"removed_empty_directories: {result['removed_empty_directories_count']}")
