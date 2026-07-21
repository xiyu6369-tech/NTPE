from __future__ import annotations

from pathlib import Path

from .errors import (
    BinaryContentDetectedError,
    EmptyFileError,
    FileNotFoundError,
    FileTooLargeError,
    NotAFileError,
    UnsupportedExtensionError,
)
from .models import SourceReadResult


class SourceFileReader:
    """Safely read source text files without decoding them."""

    def __init__(self, max_bytes: int = 1024 * 1024) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than zero")
        self.max_bytes = max_bytes

    def read(self, source_path: str | Path) -> SourceReadResult:
        path = Path(source_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not path.is_file():
            raise NotAFileError(f"Path is not a file: {path}")

        if path.suffix.lower() != ".txt":
            raise UnsupportedExtensionError(f"Unsupported extension: {path.suffix}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise EmptyFileError(f"File is empty: {path}")

        if file_size > self.max_bytes:
            raise FileTooLargeError(f"File exceeds max size: {path}")

        with path.open("rb") as handle:
            raw_bytes = handle.read(self.max_bytes)

        if b"\x00" in raw_bytes:
            raise BinaryContentDetectedError(f"Binary content detected: {path}")

        if len(raw_bytes) != file_size:
            raise FileTooLargeError(f"File exceeds max size: {path}")

        return SourceReadResult(
            source_path=path,
            filename=path.name,
            extension=path.suffix.lower(),
            byte_size=len(raw_bytes),
            raw_bytes=raw_bytes,
        )
