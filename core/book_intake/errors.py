class SourceFileError(Exception):
    """Base class for source file reader errors."""


class FileNotFoundError(SourceFileError):
    """Raised when the requested file does not exist."""


class NotAFileError(SourceFileError):
    """Raised when the path points to a directory instead of a file."""


class UnsupportedExtensionError(SourceFileError):
    """Raised when the file extension is not supported."""


class EmptyFileError(SourceFileError):
    """Raised when the file is empty."""


class FileTooLargeError(SourceFileError):
    """Raised when the file exceeds the configured maximum size."""


class BinaryContentDetectedError(SourceFileError):
    """Raised when null bytes indicate binary content."""


class EncodingError(SourceFileError):
    """Base class for encoding-related errors."""


class EncodingNotDetectedError(EncodingError):
    """Raised when no supported encoding can be determined."""


class DecodeFailedError(EncodingError):
    """Raised when decoding fails with strict semantics."""


class AmbiguousEncodingError(EncodingError):
    """Raised when multiple encodings are plausible and no deterministic choice is safe."""

    def __init__(self, message: str, candidates: tuple[str, ...] | None = None) -> None:
        super().__init__(message)
        self.candidates = candidates or ()


class UnsupportedEncodingError(EncodingError):
    """Raised when the requested encoding is not supported by the decoder."""
