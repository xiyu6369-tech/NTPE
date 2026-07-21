from pathlib import Path

import pytest

from core.book_intake.errors import (
    BinaryContentDetectedError,
    EmptyFileError,
    FileNotFoundError as SourceFileNotFoundError,
    FileTooLargeError,
    NotAFileError,
    UnsupportedExtensionError,
)
from core.book_intake.models import SourceReadResult
from core.book_intake.source_reader import SourceFileReader


@pytest.fixture
def reader(tmp_path: Path) -> SourceFileReader:
    return SourceFileReader(max_bytes=16)


def test_reads_plain_text_file(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "sample.txt"
    path.write_bytes(b"hello world")

    result = reader.read(path)

    assert isinstance(result, SourceReadResult)
    assert result.source_path == path.resolve()
    assert result.filename == "sample.txt"
    assert result.extension == ".txt"
    assert result.byte_size == 11
    assert result.raw_bytes == b"hello world"


def test_raises_for_missing_file(tmp_path: Path, reader: SourceFileReader) -> None:
    missing = tmp_path / "missing.txt"

    with pytest.raises(SourceFileNotFoundError):
        reader.read(missing)


def test_raises_for_directory_path(tmp_path: Path, reader: SourceFileReader) -> None:
    directory = tmp_path / "folder"
    directory.mkdir()

    with pytest.raises(NotAFileError):
        reader.read(directory)


def test_raises_for_unsupported_extension(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "sample.md"
    path.write_bytes(b"hello")

    with pytest.raises(UnsupportedExtensionError):
        reader.read(path)


def test_raises_for_empty_file(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")

    with pytest.raises(EmptyFileError):
        reader.read(path)


def test_raises_for_file_too_large(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "large.txt"
    path.write_bytes(b"12345678901234567")

    with pytest.raises(FileTooLargeError):
        reader.read(path)


def test_raises_for_binary_content(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "binary.txt"
    path.write_bytes(b"hello\x00world")

    with pytest.raises(BinaryContentDetectedError):
        reader.read(path)


def test_reports_size_and_raw_bytes_exactly(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "payload.txt"
    payload = b"abc\n123"
    path.write_bytes(payload)

    result = reader.read(path)

    assert result.byte_size == len(payload)
    assert result.raw_bytes == payload


def test_result_is_immutable(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "sample.txt"
    path.write_bytes(b"hello")

    result = reader.read(path)

    with pytest.raises((AttributeError, TypeError)):
        result.source_path = Path("other")


def test_pathlib_path_is_normalized(tmp_path: Path, reader: SourceFileReader) -> None:
    path = tmp_path / "nested" / "sample.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"ok")

    result = reader.read(path)

    assert result.source_path == path.resolve()


class TestCustomErrorNames:
    def test_error_names_are_explicit(self) -> None:
        assert SourceFileNotFoundError.__name__ == "FileNotFoundError"
        assert NotAFileError.__name__ == "NotAFileError"
        assert UnsupportedExtensionError.__name__ == "UnsupportedExtensionError"
        assert EmptyFileError.__name__ == "EmptyFileError"
        assert FileTooLargeError.__name__ == "FileTooLargeError"
        assert BinaryContentDetectedError.__name__ == "BinaryContentDetectedError"
