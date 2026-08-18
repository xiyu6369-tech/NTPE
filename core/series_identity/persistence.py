from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import compute_manifest_fingerprint, to_canonical_json
from .manifest import SeriesManifest


def get_series_dir(output_root: Path, series_id: str) -> Path:
    """Get the series directory path."""
    return output_root / "series" / series_id


def manifest_file_path(series_dir: Path, series_id: str) -> Path:
    """Get the manifest file path."""
    return series_dir / f"series_manifest_{series_id}.json"


def save_manifest(manifest: SeriesManifest, manifest_path: Path) -> None:
    """
    Save SeriesManifest to disk with validation.

    Writes deterministic canonical JSON with manifest_fingerprint.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure fingerprint is set
    if not manifest.manifest_fingerprint:
        fingerprint = compute_manifest_fingerprint(manifest.to_canonical_dict())
        manifest = manifest.with_fingerprint(fingerprint)

    canonical_json = to_canonical_json(manifest.to_dict(include_manifest_fingerprint=True))
    manifest_path.write_text(canonical_json, encoding="utf-8", newline="\n")


def load_manifest(manifest_path: Path) -> SeriesManifest:
    """
    Load SeriesManifest from disk with fail-closed validation.

    Raises:
        ValidationError: If file not found, invalid JSON, or schema mismatch
        IntegrityError: If manifest_fingerprint doesn't match
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    content = manifest_path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Manifest file is empty: {manifest_path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {manifest_path}") from exc

    return SeriesManifest.from_dict(data)


def ensure_series_dir(output_root: Path, series_id: str) -> Path:
    """Ensure series directory exists and return path."""
    series_dir = get_series_dir(output_root, series_id)
    series_dir.mkdir(parents=True, exist_ok=True)
    return series_dir
