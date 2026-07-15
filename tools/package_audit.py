"""Build a manifest-allowlisted NTPE audit evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile


class PackageError(RuntimeError):
    """Raised when an audit package violates a delivery boundary."""


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\bnvapi-[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"(?i)\b(?:NVIDIA_API_KEY|OPENAI_API_KEY)\s*=\s*['\"]?(?!REDACTED|YOUR_|<)[A-Za-z0-9_-]{16,}"),
)
SENSITIVE_NAMES = {
    ".env",
    "config.json",
    "credentials",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "private_key",
    "secrets",
    "secrets.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalise_relative(raw: object) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise PackageError(f"unsafe or non-portable manifest path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PackageError(f"unsafe relative manifest path: {raw!r}")
    if path.parts and ":" in path.parts[0]:
        raise PackageError(f"drive-qualified manifest path: {raw!r}")
    return path.as_posix()


def _reject_path(relative: str) -> None:
    lower_parts = [part.lower() for part in PurePosixPath(relative).parts]
    if ".git" in lower_parts:
        raise PackageError(f"Git internals are forbidden: {relative}")
    if lower_parts[-1].endswith(".zip"):
        raise PackageError(f"nested ZIP files are forbidden: {relative}")
    if any(part in SENSITIVE_NAMES for part in lower_parts):
        raise PackageError(f"sensitive path is forbidden: {relative}")
    joined = "/".join(lower_parts)
    if any(marker in joined for marker in ("private-key", "private_key", "api_key", "credentials")):
        raise PackageError(f"sensitive path is forbidden: {relative}")


def _contains_secret(path: Path) -> bool:
    content = path.read_bytes()
    return any(pattern.search(content) for pattern in SECRET_PATTERNS)


def load_manifest(root: Path, manifest: Path) -> list[tuple[str, Path, str]]:
    """Validate JSON structure, paths, hashes, and allowlisted file contents."""
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise PackageError("manifest schema_version must be '1.0'")
    entries = raw.get("files")
    if not isinstance(entries, list) or not entries:
        raise PackageError("manifest must contain a non-empty explicit files allowlist")
    if set(raw) != {"schema_version", "files"}:
        raise PackageError("manifest contains unsupported top-level fields")

    root = root.resolve()
    selected: list[tuple[str, Path, str]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise PackageError("each manifest entry must contain only path and sha256")
        relative = _normalise_relative(entry["path"])
        _reject_path(relative)
        expected = entry["sha256"]
        if not isinstance(expected, str) or not SHA256_PATTERN.fullmatch(expected):
            raise PackageError(f"invalid SHA-256 for {relative}")
        key = relative.casefold()
        if key in seen:
            raise PackageError(f"duplicate manifest path: {relative}")
        source = root.joinpath(*PurePosixPath(relative).parts)
        if source.is_symlink():
            raise PackageError(f"symbolic links are not packaged: {relative}")
        try:
            resolved = source.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise PackageError(f"missing or escaping manifest path: {relative}") from exc
        if not resolved.is_file():
            raise PackageError(f"manifest path is not a regular file: {relative}")
        actual = sha256_file(resolved)
        if actual != expected:
            raise PackageError(f"SHA-256 mismatch for {relative}")
        if _contains_secret(resolved):
            raise PackageError(f"secret-like content detected in {relative}")
        selected.append((relative, resolved, expected))
        seen.add(key)
    selected.sort(key=lambda item: item[0].casefold())
    return selected


def build_audit_package(root: Path, manifest: Path, output: Path) -> dict[str, object]:
    """Build an Audit Package using only the manifest's explicit allowlist."""
    root = root.resolve()
    files = load_manifest(root, manifest.resolve())
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, source, _ in files:
                archive.write(source, arcname=relative)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    expected = {relative: digest for relative, _, digest in files}
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            raise PackageError("ZIP integrity verification failed")
        if names != list(expected) or any("\\" in name for name in names):
            raise PackageError("ZIP entry names did not round-trip safely")
        if len({name.casefold() for name in names}) != len(names):
            raise PackageError("duplicate ZIP entry names detected")
        for info in archive.infolist():
            if not info.filename.isascii() and not (info.flag_bits & 0x800):
                raise PackageError("Unicode ZIP entry is missing the UTF-8 flag")
            if hashlib.sha256(archive.read(info)).hexdigest() != expected[info.filename]:
                raise PackageError(f"packaged SHA-256 mismatch for {info.filename}")
    return {
        "package_type": "audit",
        "output": str(output),
        "entries": len(files),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "manifest_validation": "PASS",
        "integrity": "PASS",
        "path_separator_validation": "PASS",
        "unicode_round_trip": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        result = build_audit_package(root, manifest, output)
        if args.report:
            report = args.report if args.report.is_absolute() else root / args.report
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (PackageError, OSError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
