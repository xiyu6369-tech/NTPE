from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from core.shared.evidence.hashing import (
    is_sha256_hex,
    require_sha256_hex,
    sha256_bytes,
    sha256_file,
    sha256_text,
)


def test_bytes_text_and_empty_hashes() -> None:
    assert sha256_bytes(b"") == hashlib.sha256(b"").hexdigest()
    assert sha256_bytes(b"evidence") == hashlib.sha256(b"evidence").hexdigest()
    assert sha256_text("證據") == hashlib.sha256("證據".encode()).hexdigest()


def test_file_hash_streams_large_file(tmp_path: Path) -> None:
    content = (b"0123456789abcdef" * 131_073) + b"tail"
    path = tmp_path / "large.bin"
    path.write_bytes(content)
    assert sha256_file(path, chunk_size=4093) == hashlib.sha256(content).hexdigest()


def test_file_hash_rejects_invalid_inputs(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        sha256_file(file_path, chunk_size=0)
    with pytest.raises(FileNotFoundError):
        sha256_file(tmp_path / "missing")
    with pytest.raises(IsADirectoryError):
        sha256_file(tmp_path)


def test_sha_validation_is_strict() -> None:
    valid = hashlib.sha256(b"valid").hexdigest()
    assert is_sha256_hex(valid)
    assert require_sha256_hex(valid) == valid
    for invalid in (valid.upper(), "", valid[:-1], "g" * 64, f" {valid}", None, 123):
        assert not is_sha256_hex(invalid)
        with pytest.raises(ValueError):
            require_sha256_hex(invalid, field_name="artifact_sha256")


def test_hash_input_types_are_not_coerced() -> None:
    with pytest.raises(TypeError):
        sha256_bytes(bytearray(b"x"))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        sha256_text(b"x")  # type: ignore[arg-type]

