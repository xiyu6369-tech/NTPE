"""Stable evidence serialization, hashing, and path contracts."""

from .canonical_json import (
    canonical_json_bytes,
    canonical_json_text,
    read_json,
    write_canonical_json,
)
from .hashing import (
    is_sha256_hex,
    require_sha256_hex,
    sha256_bytes,
    sha256_file,
    sha256_text,
)
from .paths import (
    normalize_project_relative_path,
    require_path_within_root,
    resolve_project_relative_path,
)

__all__ = [
    "canonical_json_bytes",
    "canonical_json_text",
    "is_sha256_hex",
    "normalize_project_relative_path",
    "read_json",
    "require_path_within_root",
    "require_sha256_hex",
    "resolve_project_relative_path",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
    "write_canonical_json",
]

