"""Resolve and bind the exact authentic three-chunk Stage 7.4 excerpt."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from core.book_intake import BookIntakeProcessor
from core.controlled_runtime_scheduling_dispatch import (
    ControlledRuntimeDispatchPackage,
)
from core.controlled_translation_runtime_integration.policy import (
    ControlledTranslationExecutionPolicy,
)
from core.controlled_translation_runtime_integration.serialization import (
    canonical_sha256,
)
from lts.txt_translation_runtime import split_text

from .errors import ControlledMultiChunkAuthorityError, ControlledMultiChunkResolutionError
from .models import ChunkExecutionPlan, MultiChunkCanaryRequest
from .policy import (
    ATTEMPT_CAP, CHUNK_CHARACTER_COUNTS, CHUNK_COUNT, CHUNK_FINGERPRINTS,
    CHUNK_SIZE, CONNECT_TIMEOUT_SECONDS, INTENT, OUTPUT_ROOT, PROFILE,
    READ_TIMEOUT_SECONDS, REQUEST_CAP, SOURCE_CHARACTER_COUNT,
    SOURCE_DECODED_TEXT_FINGERPRINT, SOURCE_FINGERPRINT,
    SOURCE_FINGERPRINT_TYPE, SOURCE_FIXTURE_ID, SOURCE_FIXTURE_PATH,
    SOURCE_NEWLINE_NORMALIZED_FINGERPRINT, SOURCE_RAW_BYTE_FINGERPRINT,
    TARGET_LANGUAGE,
)


@dataclass(frozen=True)
class SourceFixtureFingerprints:
    raw_byte_sha256: str
    decoded_text_sha256: str
    newline_normalized_sha256: str
    canonical_source_sha256: str


@dataclass(frozen=True)
class ResolvedMultiChunkSource:
    source_text: str
    chunks: tuple[str, ...]
    plans: tuple[ChunkExecutionPlan, ...]


def fingerprint_source_fixture(path: str | Path) -> SourceFixtureFingerprints:
    """Return every declared Stage 7.4 fixture fingerprint representation."""
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return SourceFixtureFingerprints(
        raw_byte_sha256=hashlib.sha256(raw).hexdigest(),
        decoded_text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        newline_normalized_sha256=hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest(),
        canonical_source_sha256=canonical_sha256(text),
    )


def resolve_multi_chunk_source(
    dispatch_package: ControlledRuntimeDispatchPackage, *, root: str | Path,
) -> ResolvedMultiChunkSource:
    if not isinstance(dispatch_package, ControlledRuntimeDispatchPackage):
        raise ControlledMultiChunkAuthorityError("authentic Stage 7.2 dispatch required")
    base = Path(root).resolve()
    path = (base / SOURCE_FIXTURE_PATH).resolve()
    if base not in path.parents or not path.is_file():
        raise ControlledMultiChunkResolutionError("authorized Stage 7.4 source unavailable")
    fixture_fingerprints = fingerprint_source_fixture(path)
    if (
        fixture_fingerprints.raw_byte_sha256 != SOURCE_RAW_BYTE_FINGERPRINT
        or fixture_fingerprints.decoded_text_sha256
        != SOURCE_DECODED_TEXT_FINGERPRINT
        or fixture_fingerprints.newline_normalized_sha256
        != SOURCE_NEWLINE_NORMALIZED_FINGERPRINT
        or fixture_fingerprints.canonical_source_sha256 != SOURCE_FINGERPRINT
    ):
        raise ControlledMultiChunkResolutionError("Stage 7.4 fixture bytes mismatch")
    intake = BookIntakeProcessor().process(path)
    text = intake.text
    chunks = tuple(split_text(text, CHUNK_SIZE))
    fingerprints = tuple(canonical_sha256(chunk) for chunk in chunks)
    if (
        intake.status not in {"ready", "ready_with_warnings"}
        or intake.language_result.language != "ko"
        or len(text) != SOURCE_CHARACTER_COUNT
        or canonical_sha256(text) != SOURCE_FINGERPRINT
        or len(chunks) != CHUNK_COUNT
        or tuple(map(len, chunks)) != CHUNK_CHARACTER_COUNTS
        or fingerprints != CHUNK_FINGERPRINTS
    ):
        raise ControlledMultiChunkResolutionError("Stage 7.4 source identity mismatch")
    starts: list[int] = []
    cursor = 0
    for chunk in chunks:
        start = text.find(chunk, cursor)
        if start < cursor:
            raise ControlledMultiChunkResolutionError("chunk order or range invalid")
        starts.append(start)
        cursor = start + len(chunk)
    chunk_ids = tuple(
        f"stage74-chunk-{index:03d}-{fingerprint[:16]}"
        for index, fingerprint in enumerate(fingerprints, 1)
    )
    plans = tuple(
        ChunkExecutionPlan(
            index=index,
            chunk_id=chunk_ids[index - 1],
            chunk_fingerprint=fingerprints[index - 1],
            source_start=starts[index - 1],
            source_end=starts[index - 1] + len(chunks[index - 1]),
            source_character_count=len(chunks[index - 1]),
            source_fixture_id=SOURCE_FIXTURE_ID,
            source_fingerprint=SOURCE_FINGERPRINT,
            previous_chunk_id=chunk_ids[index - 2] if index > 1 else "",
            next_chunk_id=chunk_ids[index] if index < CHUNK_COUNT else "",
            target_language=TARGET_LANGUAGE,
            literary_profile=PROFILE,
            work_package_reference_fingerprint=(
                dispatch_package.work_package_reference_fingerprint
            ),
            output_artifact_path=f"chunk-{index:03d}.translated.txt",
            checkpoint_artifact_path=f"checkpoint-{index:03d}.json",
        )
        for index in range(1, CHUNK_COUNT + 1)
    )
    return ResolvedMultiChunkSource(text, chunks, plans)


def build_multi_chunk_request(
    dispatch_package: ControlledRuntimeDispatchPackage,
    plans: tuple[ChunkExecutionPlan, ...],
) -> MultiChunkCanaryRequest:
    if not isinstance(dispatch_package, ControlledRuntimeDispatchPackage):
        raise ControlledMultiChunkAuthorityError("authentic Stage 7.2 dispatch required")
    if len(plans) != CHUNK_COUNT:
        raise ControlledMultiChunkResolutionError("exactly three plans required")
    return MultiChunkCanaryRequest(
        stage73_policy_fingerprint=canonical_sha256(
            asdict(ControlledTranslationExecutionPolicy())
        ),
        dispatch_package_id=dispatch_package.dispatch_package_id,
        dispatch_fingerprint=dispatch_package.dispatch_fingerprint,
        schedule_id=dispatch_package.schedule_id,
        schedule_fingerprint=dispatch_package.schedule_fingerprint,
        queue_record_id=dispatch_package.queue_record_id,
        queue_record_fingerprint=dispatch_package.queue_record_fingerprint,
        authenticated_lineage=tuple(dispatch_package.canonical_chain),
        source_fixture_id=SOURCE_FIXTURE_ID,
        source_fingerprint=SOURCE_FINGERPRINT,
        source_fingerprint_type=SOURCE_FINGERPRINT_TYPE,
        complete_source_fingerprint=SOURCE_FINGERPRINT,
        complete_source_fingerprint_type=SOURCE_FINGERPRINT_TYPE,
        target_language=TARGET_LANGUAGE,
        literary_profile=PROFILE,
        chunk_count=CHUNK_COUNT,
        chunk_ids=tuple(plan.chunk_id for plan in plans),
        chunk_fingerprints=tuple(plan.chunk_fingerprint for plan in plans),
        provider_request_cap=REQUEST_CAP,
        provider_attempt_cap=ATTEMPT_CAP,
        connect_timeout_seconds=CONNECT_TIMEOUT_SECONDS,
        read_timeout_seconds=READ_TIMEOUT_SECONDS,
        artifact_root=OUTPUT_ROOT,
        intent=INTENT,
    )
