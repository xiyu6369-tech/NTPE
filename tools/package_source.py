"""Build the deliberately narrow NTPE source-delivery package."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.shared.evidence import (
    normalize_project_relative_path,
    require_path_within_root,
    sha256_file,
    write_canonical_json,
)


class PackageError(RuntimeError):
    """Raised when a package would cross a delivery boundary."""


INCLUDED_ROOTS = {
    "cli",
    "compatibility",
    "config",
    "core",
    "data",
    "docs/architecture",
    "engine",
    "external_api",
    "gui",
    "integration",
    "lts",
    "packaging",
    "platform_services",
    "profiles",
    "rules",
    "runtime_api",
    "schemas",
    "sdk",
    "tools",
    "translation",
    "web_ui",
    "workflow",
}

INCLUDED_ROOT_FILES = {
    "LICENSE",
    "LICENSE.md",
    "README.md",
    "character_database_override.json",
    "character_override.json",
    "glossary_override.json",
    "launcher_translate.py",
    "ntpe_literary_evaluation.py",
    "ntpe_literary_regression.py",
    "ntpe_production_translate.py",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
}

EXCLUDED_COMPONENTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "analysis",
    "artifacts",
    "audits",
    "backup",
    "cache",
    "dist",
    "docs/archive",
    "docs/releases",
    "failed_chunks",
    "final_output",
    "input",
    "logs",
    "manifests",
    "memory",
    "output",
    "prompt_packages",
    "quality_reports",
    "release",
    "reports",
    "sessions",
    "tests",
    "tests/literary/outputs",
    "tmp",
    "translated",
    "translation_cache",
}

EXCLUDED_SUFFIXES = {".bak", ".pyc", ".pyo", ".zip"}
SENSITIVE_NAMES = {
    ".env",
    "config.json",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "private_key",
    "secrets",
    "secrets.json",
}


def _normalise_relative(raw: str) -> str:
    if not raw or "\\" in raw:
        raise PackageError(f"unsafe or non-portable path: {raw!r}")
    try:
        return normalize_project_relative_path(raw)
    except (TypeError, ValueError) as exc:
        raise PackageError(f"unsafe relative path: {raw!r}") from exc


def _contains_component(path: str, excluded: str) -> bool:
    parts = PurePosixPath(path).parts
    excluded_parts = PurePosixPath(excluded).parts
    size = len(excluded_parts)
    return any(parts[index : index + size] == excluded_parts for index in range(len(parts) - size + 1))


def _looks_sensitive(path: str) -> bool:
    lower_parts = [part.lower() for part in PurePosixPath(path).parts]
    if any(part in SENSITIVE_NAMES for part in lower_parts):
        return True
    joined = "/".join(lower_parts)
    return any(marker in joined for marker in ("resume_state", "private-key", "private_key", "api_key"))


def is_source_path(path: str) -> bool:
    """Return whether a safe relative path belongs in the source package."""
    path = _normalise_relative(path)
    lower = path.lower()
    if Path(lower).suffix in EXCLUDED_SUFFIXES or _looks_sensitive(lower):
        return False
    if any(_contains_component(lower, excluded) for excluded in EXCLUDED_COMPONENTS):
        return False
    parts = PurePosixPath(path).parts
    if len(parts) == 1:
        return path in INCLUDED_ROOT_FILES
    return any(lower == root or lower.startswith(root + "/") for root in INCLUDED_ROOTS)


def _run_git(root: Path, arguments: list[str], purpose: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"").decode("utf-8", "replace").strip()
        raise PackageError(f"unable to {purpose}: {detail or exc}") from exc
    return result.stdout


def _git_head(root: Path) -> str:
    raw = _run_git(root, ["rev-parse", "--verify", "HEAD"], "resolve Git HEAD")
    head = raw.decode("ascii", "strict").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise PackageError("Git HEAD is missing or invalid")
    return head


def _git_candidates(root: Path, *, include_untracked: bool = False) -> list[str]:
    arguments = ["ls-files", "-z", "--cached"]
    if include_untracked:
        arguments.extend(["--others", "--exclude-standard"])
    raw = _run_git(root, arguments, "enumerate the Git worktree")
    try:
        return [item.decode("utf-8") for item in raw.split(b"\0") if item]
    except UnicodeDecodeError as exc:
        raise PackageError("Git returned a filename that is not valid UTF-8") from exc


def collect_source_files(root: Path, *, include_untracked: bool = False) -> list[tuple[str, Path]]:
    """Select source files and prove that every selected path stays under root."""
    root = root.resolve()
    selected: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for raw in _git_candidates(root, include_untracked=include_untracked):
        relative = _normalise_relative(raw)
        if not is_source_path(relative):
            continue
        key = relative.casefold()
        if key in seen:
            raise PackageError(f"duplicate archive path: {relative}")
        source = root.joinpath(*PurePosixPath(relative).parts)
        if source.is_symlink():
            raise PackageError(f"symbolic links are not packaged: {relative}")
        try:
            resolved = require_path_within_root(root, source.resolve(strict=True))
        except (OSError, ValueError) as exc:
            raise PackageError(f"path escapes worktree: {relative}") from exc
        if not resolved.is_file():
            raise PackageError(f"not a regular file: {relative}")
        selected.append((relative, resolved))
        seen.add(key)
    selected.sort(key=lambda item: item[0].casefold())
    if not selected:
        raise PackageError("source package selection is empty")
    return selected


def _verify_zip(output: Path, expected: list[str]) -> dict[str, object]:
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            raise PackageError("ZIP integrity verification failed")
        if names != expected or any("\\" in name for name in names):
            raise PackageError("ZIP entry names did not round-trip safely")
        unicode_ok = all(
            bool(info.flag_bits & 0x800)
            for info in archive.infolist()
            if not info.filename.isascii()
        )
        if not unicode_ok:
            raise PackageError("Unicode ZIP entry is missing the UTF-8 flag")
    return {
        "integrity": "PASS",
        "path_separator_validation": "PASS",
        "unicode_round_trip": "PASS",
    }


def build_source_package(
    root: Path,
    output: Path,
    *,
    include_untracked: bool = False,
) -> dict[str, object]:
    """Build and verify a Source Package without changing the worktree."""
    root = root.resolve()
    output = output.resolve()
    git_head = _git_head(root)
    files = collect_source_files(root, include_untracked=include_untracked)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, source in files:
                archive.write(source, arcname=relative)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    verification = _verify_zip(output, [relative for relative, _ in files])
    return {
        "package_type": "source",
        "output": str(output),
        "git_head": git_head,
        "tracked_only": not include_untracked,
        "include_untracked": include_untracked,
        "entries": len(files),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        **verification,
    }


def _write_report(report: Path, result: dict[str, object]) -> None:
    write_canonical_json(report, result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("dist/NTPE_SOURCE.zip"))
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="explicitly include non-ignored untracked allowlisted files",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        result = build_source_package(root, output, include_untracked=args.include_untracked)
        if args.report:
            report = args.report if args.report.is_absolute() else root / args.report
            _write_report(report, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (PackageError, OSError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
