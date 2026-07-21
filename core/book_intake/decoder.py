from __future__ import annotations

import hashlib

from .errors import DecodeFailedError, UnsupportedEncodingError
from .models import DecodedSource, EncodingDetectionResult

_CANONICAL_ENCODINGS = {"utf-8", "utf-16-le", "utf-16-be", "cp949", "euc-kr", "shift-jis"}


def decode_source(
    raw_bytes: bytes,
    detection: EncodingDetectionResult,
    *,
    encoding: str | None = None,
    strict: bool = True,
) -> DecodedSource:
    selected_encoding = encoding or detection.encoding
    if selected_encoding not in _CANONICAL_ENCODINGS:
        raise UnsupportedEncodingError(f"Unsupported encoding: {selected_encoding}")

    if detection.bom_present and selected_encoding == "utf-8":
        decode_encoding = "utf-8-sig"
    elif detection.bom_present and selected_encoding in {"utf-16-le", "utf-16-be"}:
        decode_encoding = "utf-16"
    elif selected_encoding == "utf-16-le":
        decode_encoding = "utf-16-le"
    elif selected_encoding == "utf-16-be":
        decode_encoding = "utf-16-be"
    else:
        decode_encoding = selected_encoding

    try:
        text = raw_bytes.decode(decode_encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise DecodeFailedError(f"Decode failed for {selected_encoding}") from exc

    if "\uFFFD" in text:
        raise DecodeFailedError("Replacement character detected")

    bom_removed = bool(detection.bom_present)

    return DecodedSource(
        encoding=selected_encoding,
        text=text,
        byte_size=len(raw_bytes),
        character_count=len(text),
        bom_removed=bom_removed,
        content_hash=hashlib.sha256(raw_bytes).hexdigest(),
    )
