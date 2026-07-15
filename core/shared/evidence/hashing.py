"""SHA-256 helpers with strict evidence-format validation."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(data: bytes) -> str:
    """Hash bytes and return exactly 64 lowercase hexadecimal characters."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str, *, encoding: str = "utf-8") -> str:
    """Encode text explicitly and return its SHA-256 digest."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return sha256_bytes(text.encode(encoding))


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Stream a regular file into SHA-256 without loading it all into memory."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    if not source.is_file():
        raise IsADirectoryError(source)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def is_sha256_hex(value: object) -> bool:
    """Return whether *value* is a strict lowercase SHA-256 hex string."""
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def require_sha256_hex(value: object, *, field_name: str = "sha256") -> str:
    """Return a valid digest or reject it without trimming or normalizing."""
    if not is_sha256_hex(value):
        raise ValueError(f"{field_name} must be 64 lowercase hexadecimal characters")
    return value

