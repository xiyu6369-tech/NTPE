import hashlib
from pathlib import Path

import pytest

from core.controlled_multi_chunk_translation_canary import (
    ControlledMultiChunkResolutionError,
    build_multi_chunk_request,
    resolve_multi_chunk_source,
)
from core.controlled_multi_chunk_translation_canary import resolver as resolver_module
from core.controlled_multi_chunk_translation_canary.policy import (
    CHUNK_CHARACTER_COUNTS,
    CHUNK_FINGERPRINTS,
    SOURCE_CANONICAL_FINGERPRINT,
    SOURCE_CHARACTER_COUNT,
    SOURCE_DECODED_TEXT_FINGERPRINT,
    SOURCE_DECODED_TEXT_FINGERPRINT_TYPE,
    SOURCE_FINGERPRINT,
    SOURCE_FINGERPRINT_TYPE,
    SOURCE_FIXTURE_PATH,
    SOURCE_NEWLINE_NORMALIZED_FINGERPRINT,
    SOURCE_NEWLINE_NORMALIZED_FINGERPRINT_TYPE,
    SOURCE_RAW_BYTE_FINGERPRINT,
    SOURCE_RAW_BYTE_FINGERPRINT_TYPE,
)
from core.controlled_multi_chunk_translation_canary.resolver import (
    fingerprint_source_fixture,
)
from tests.unit.controlled_multi_chunk_translation_canary import build_context


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPOSITORY_ROOT / SOURCE_FIXTURE_PATH


def _copy_fixture(tmp_path: Path, payload: bytes) -> Path:
    destination = tmp_path / SOURCE_FIXTURE_PATH
    destination.parent.mkdir(parents=True)
    destination.write_bytes(payload)
    return destination


def test_fixture_fingerprint_representations_are_explicit_and_exact():
    fingerprints = fingerprint_source_fixture(FIXTURE_PATH)
    assert fingerprints.raw_byte_sha256 == SOURCE_RAW_BYTE_FINGERPRINT
    assert fingerprints.decoded_text_sha256 == SOURCE_DECODED_TEXT_FINGERPRINT
    assert (
        fingerprints.newline_normalized_sha256
        == SOURCE_NEWLINE_NORMALIZED_FINGERPRINT
    )
    assert fingerprints.canonical_source_sha256 == SOURCE_CANONICAL_FINGERPRINT
    assert SOURCE_RAW_BYTE_FINGERPRINT_TYPE == "sha256-raw-bytes-v1"
    assert SOURCE_DECODED_TEXT_FINGERPRINT_TYPE == "sha256-utf8-text-v1"
    assert (
        SOURCE_NEWLINE_NORMALIZED_FINGERPRINT_TYPE
        == "sha256-utf8-lf-text-v1"
    )
    assert SOURCE_FINGERPRINT == SOURCE_CANONICAL_FINGERPRINT
    assert SOURCE_FINGERPRINT_TYPE == "sha256-canonical-json-v1"
    assert len(FIXTURE_PATH.read_text(encoding="utf-8")) == SOURCE_CHARACTER_COUNT


def test_authentic_chunk_and_request_fingerprints_are_deterministic(tmp_path):
    context = build_context(tmp_path)
    resolved = resolve_multi_chunk_source(
        context["dispatch_package"], root=context["repository_root"]
    )
    request = build_multi_chunk_request(context["dispatch_package"], resolved.plans)
    assert [(plan.source_start, plan.source_end) for plan in resolved.plans] == [
        (0, 575),
        (577, 1117),
        (1119, 1633),
    ]
    assert resolved.source_text == "\n\n".join(resolved.chunks)
    assert [
        resolved.source_text[current.source_end:following.source_start]
        for current, following in zip(resolved.plans, resolved.plans[1:])
    ] == ["\n\n", "\n\n"]
    assert tuple(plan.source_character_count for plan in resolved.plans) == (
        CHUNK_CHARACTER_COUNTS
    )
    assert tuple(plan.chunk_fingerprint for plan in resolved.plans) == (
        CHUNK_FINGERPRINTS
    )
    assert tuple(plan.chunk_id for plan in resolved.plans) == (
        "stage74-chunk-001-5be537c45817ccc7",
        "stage74-chunk-002-542e4c34fccaac7a",
        "stage74-chunk-003-8527171c147f77e3",
    )
    assert request.source_fingerprint == SOURCE_CANONICAL_FINGERPRINT
    assert request.complete_source_fingerprint == SOURCE_CANONICAL_FINGERPRINT
    assert request.source_fingerprint_type == SOURCE_FINGERPRINT_TYPE
    assert request.complete_source_fingerprint_type == SOURCE_FINGERPRINT_TYPE


def test_raw_fixture_byte_drift_fails_closed(tmp_path):
    changed = FIXTURE_PATH.read_bytes() + b" "
    _copy_fixture(tmp_path, changed)
    context = build_context(tmp_path / "context")
    with pytest.raises(
        ControlledMultiChunkResolutionError, match="fixture bytes mismatch"
    ):
        resolve_multi_chunk_source(context["dispatch_package"], root=tmp_path)


def test_newline_only_change_preserves_canonical_hash_but_fails_raw_contract(
    tmp_path,
):
    original = FIXTURE_PATH.read_bytes()
    changed = original.replace(b"\n", b"\r\n")
    changed_path = _copy_fixture(tmp_path, changed)
    fingerprints = fingerprint_source_fixture(changed_path)
    assert fingerprints.raw_byte_sha256 != SOURCE_RAW_BYTE_FINGERPRINT
    assert (
        fingerprints.newline_normalized_sha256
        == SOURCE_NEWLINE_NORMALIZED_FINGERPRINT
    )
    assert fingerprints.canonical_source_sha256 == SOURCE_CANONICAL_FINGERPRINT
    context = build_context(tmp_path / "context")
    with pytest.raises(
        ControlledMultiChunkResolutionError, match="fixture bytes mismatch"
    ):
        resolve_multi_chunk_source(context["dispatch_package"], root=tmp_path)


def test_raw_or_decoded_hash_cannot_replace_canonical_request_hash(
    tmp_path, monkeypatch,
):
    assert hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest() == (
        SOURCE_RAW_BYTE_FINGERPRINT
    )
    context = build_context(tmp_path)
    monkeypatch.setattr(
        resolver_module, "SOURCE_FINGERPRINT", SOURCE_RAW_BYTE_FINGERPRINT
    )
    with pytest.raises(
        ControlledMultiChunkResolutionError, match="fixture bytes mismatch"
    ):
        resolve_multi_chunk_source(
            context["dispatch_package"], root=context["repository_root"]
        )
